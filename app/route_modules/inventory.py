from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def register_routes(main):
    @main.route("/inventory")
    @login_required
    def inventory():
        items = []
        search = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "").strip()
        try:
            with db_cursor() as (connection, cursor):
                refresh_system_alerts(cursor, connection)
                query = "SELECT * FROM inventory_items WHERE 1=1"
                params = []
                if search:
                    query += " AND (item_name LIKE %s OR CAST(item_id AS CHAR) LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%"])
                if category in ITEM_CATEGORIES:
                    query += " AND category = %s"
                    params.append(category)
                if status == "in_stock":
                    query += " AND quantity > minimum_stock"
                elif status == "low_stock":
                    query += " AND quantity > 0 AND quantity <= minimum_stock"
                elif status == "out_of_stock":
                    query += " AND quantity = 0"
                query += " ORDER BY item_id DESC"
                cursor.execute(query, params)
                items = cursor.fetchall()
        except Error:
            flash("Error loading inventory.", "danger")
        return render_template(
            "inventory.html",
            items=items,
            current_search=search,
            current_category=category,
            current_status=status,
        )
    
    
    @main.route("/inventory/add", methods=["POST"])
    @role_required("admin", "manager")
    def inventory_add():
        try:
            item_name = request.form.get("item_name", "").strip()
            category = request.form.get("category", "")
            quantity = decimal_form("quantity", "Quantity")
            unit = request.form.get("unit", "").strip()
            min_stock = decimal_form("minimum_stock", "Minimum stock")
            if not item_name or not unit or category not in ITEM_CATEGORIES:
                raise ValueError("Please provide valid inventory details.")
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    """
                    INSERT INTO inventory_items (item_name, category, quantity, unit, minimum_stock)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (item_name, category, quantity, unit, min_stock),
                )
                connection.commit()
                item_id = cursor.lastrowid
                refresh_system_alerts(cursor, connection)
            log_audit("create", "inventory_item", item_id, f"Added {item_name}.")
            flash("Item added successfully.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Error adding item.", "danger")
        return redirect(url_for("main.inventory"))
    
    
    @main.route("/inventory/edit/<int:item_id>", methods=["POST"])
    @role_required("admin", "manager")
    def inventory_edit(item_id):
        try:
            item_name = request.form.get("item_name", "").strip()
            category = request.form.get("category", "")
            quantity = decimal_form("quantity", "Quantity")
            unit = request.form.get("unit", "").strip()
            min_stock = decimal_form("minimum_stock", "Minimum stock")
            if not item_name or not unit or category not in ITEM_CATEGORIES:
                raise ValueError("Please provide valid inventory details.")
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    """
                    UPDATE inventory_items
                    SET item_name = %s, category = %s, quantity = %s, unit = %s, minimum_stock = %s
                    WHERE item_id = %s
                    """,
                    (item_name, category, quantity, unit, min_stock, item_id),
                )
                connection.commit()
                refresh_system_alerts(cursor, connection)
            log_audit("update", "inventory_item", item_id, f"Updated {item_name}.")
            flash("Item updated successfully.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Error updating item.", "danger")
        return redirect(url_for("main.inventory"))
    
    
    @main.route("/inventory/delete/<int:item_id>", methods=["POST"])
    @role_required("admin", "manager")
    def inventory_delete(item_id):
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute("DELETE FROM inventory_items WHERE item_id = %s", (item_id,))
                connection.commit()
                refresh_system_alerts(cursor, connection)
            log_audit("delete", "inventory_item", item_id, "Deleted inventory item.")
            flash("Item deleted successfully.", "success")
        except Error:
            flash("Error deleting item. It may be linked to deliveries.", "danger")
        return redirect(url_for("main.inventory"))
    
    
    @main.route("/inventory/quick_update/<int:item_id>", methods=["POST"])
    @role_required("admin", "manager")
    def inventory_quick_update(item_id):
        try:
            quantity = decimal_form("quantity", "Quantity")
            with db_cursor() as (connection, cursor):
                cursor.execute("UPDATE inventory_items SET quantity = %s WHERE item_id = %s", (quantity, item_id))
                connection.commit()
                refresh_system_alerts(cursor, connection)
            log_audit("quick_update", "inventory_item", item_id, f"Quantity set to {quantity}.")
            flash("Quantity updated successfully.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Error updating quantity.", "danger")
        return redirect(url_for("main.inventory"))
