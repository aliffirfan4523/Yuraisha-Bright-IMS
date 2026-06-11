from datetime import date, datetime, timedelta
import csv
import io

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

from app.route_support import *

def register_routes(main):
    @main.route("/inventory")
    @login_required
    def inventory():
        materials = []
        search = request.args.get("q", "").strip()
        status = request.args.get("status", "").strip()
        try:
            with db_cursor() as (connection, cursor):
                query = "SELECT * FROM tbl_material WHERE 1=1"
                params = []
                if search:
                    query += " AND (material_name LIKE %s OR CAST(material_id AS CHAR) LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%"])
                if status == "in_stock":
                    query += " AND current_quantity > low_stock_threshold"
                elif status == "low_stock":
                    query += " AND current_quantity > 0 AND current_quantity <= low_stock_threshold"
                elif status == "out_of_stock":
                    query += " AND current_quantity = 0"
                query += " ORDER BY material_id DESC"
                cursor.execute(query, params)
                materials = cursor.fetchall()
                # Rename keys for template compatibility if needed
                for m in materials:
                    m["item_id"] = m["material_id"]
                    m["item_name"] = m["material_name"]
                    m["quantity"] = m["current_quantity"]
                    m["minimum_stock"] = m["low_stock_threshold"]
                    m["updated_at"] = m["last_updated"]
        except Error:
            flash("Error loading inventory.", "danger")
        return render_template(
            "inventory.html",
            items=materials,
            current_search=search,
            current_status=status,
            category_labels={},
            category_order=[],
        )
    
    @main.route("/inventory/add", methods=["POST"])
    @role_required("admin", "manager")
    def inventory_add():
        try:
            item_name = request.form.get("item_name", "").strip()
            quantity = decimal_form("quantity", "Quantity")
            min_stock = decimal_form("minimum_stock", "Low stock threshold")
            if not item_name:
                raise ValueError("Please provide a valid material name.")
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    """
                    INSERT INTO tbl_material (material_name, current_quantity, low_stock_threshold)
                    VALUES (%s, %s, %s)
                    """,
                    (item_name, quantity, min_stock),
                )
                connection.commit()
                item_id = cursor.lastrowid
            log_audit("create", "material", item_id, f"Added {item_name}.")
            flash("Material added successfully.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Error adding material.", "danger")
        return redirect(url_for("main.inventory"))
    
    @main.route("/inventory/edit/<int:item_id>", methods=["POST"])
    @role_required("admin", "manager")
    def inventory_edit(item_id):
        try:
            item_name = request.form.get("item_name", "").strip()
            quantity = decimal_form("quantity", "Quantity")
            min_stock = decimal_form("minimum_stock", "Low stock threshold")
            if not item_name:
                raise ValueError("Please provide a valid material name.")
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    """
                    UPDATE tbl_material
                    SET material_name = %s, current_quantity = %s, low_stock_threshold = %s
                    WHERE material_id = %s
                    """,
                    (item_name, quantity, min_stock, item_id),
                )
                connection.commit()
            log_audit("update", "material", item_id, f"Updated {item_name}.")
            flash("Material updated successfully.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Error updating material.", "danger")
        return redirect(url_for("main.inventory"))
    
    @main.route("/inventory/delete/<int:item_id>", methods=["POST"])
    @role_required("admin", "manager")
    def inventory_delete(item_id):
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute("DELETE FROM tbl_material WHERE material_id = %s", (item_id,))
                connection.commit()
            log_audit("delete", "material", item_id, "Deleted material.")
            flash("Material deleted successfully.", "success")
        except Error:
            flash("Error deleting material. It may be linked to deliveries.", "danger")
        return redirect(url_for("main.inventory"))

    @main.route("/inventory/quick_update/<int:item_id>", methods=["POST"])
    @role_required("admin", "manager")
    def inventory_quick_update(item_id):
        try:
            quantity = decimal_form("quantity", "Quantity")
            with db_cursor() as (connection, cursor):
                cursor.execute("UPDATE tbl_material SET current_quantity = %s WHERE material_id = %s", (quantity, item_id))
                connection.commit()
            log_audit("quick_update", "material", item_id, f"Quantity set to {quantity}.")
            flash("Quantity updated successfully.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Error updating quantity.", "danger")
        return redirect(url_for("main.inventory"))
