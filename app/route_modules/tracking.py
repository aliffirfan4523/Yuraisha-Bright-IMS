from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def register_routes(main):
    @main.route("/tracking")
    @login_required
    def tracking():
        deliveries = []
        items = []
        status = request.args.get("status", "")
        movement_type = request.args.get("movement_type", "")
        search = request.args.get("q", "").strip()
        try:
            with db_cursor() as (connection, cursor):
                refresh_system_alerts(cursor, connection)
                cursor.execute("SELECT item_id, item_name FROM inventory_items ORDER BY item_name")
                items = cursor.fetchall()
                query = """
                    SELECT d.*, i.item_name
                    FROM supplier_deliveries d
                    LEFT JOIN inventory_items i ON d.item_id = i.item_id
                    WHERE 1=1
                """
                params = []
                if status in DELIVERY_STATUSES:
                    query += " AND d.status = %s"
                    params.append(status)
                if movement_type in MOVEMENT_TYPES:
                    query += " AND d.movement_type = %s"
                    params.append(movement_type)
                if search:
                    query += " AND (d.supplier_name LIKE %s OR i.item_name LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%"])
                query += " ORDER BY d.expected_date DESC, d.delivery_id DESC"
                cursor.execute(query, params)
                deliveries = cursor.fetchall()
        except Error:
            flash("Could not load delivery tracking.", "danger")
        return render_template(
            "tracking.html",
            deliveries=deliveries,
            items=items,
            current_status=status,
            current_movement_type=movement_type,
            current_search=search,
        )
    
    
    @main.route("/tracking/add", methods=["POST"])
    @role_required("admin", "manager")
    def tracking_add():
        try:
            supplier_name = request.form.get("supplier_name", "").strip()
            movement_type = request.form.get("movement_type", "inbound")
            item_id = int_form("item_id", "Item", 1)
            quantity = decimal_form("quantity", "Quantity", 0.01)
            expected_date = date_form("expected_date", "Expected date")
            received_date = date_form("received_date", "Received date")
            status = request.form.get("status", "pending")
            if not supplier_name or status not in DELIVERY_STATUSES or movement_type not in MOVEMENT_TYPES:
                raise ValueError("Please provide valid delivery details.")
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    """
                    INSERT INTO supplier_deliveries
                    (movement_type, supplier_name, item_id, quantity, expected_date, received_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (movement_type, supplier_name, item_id, quantity, expected_date, received_date, status),
                )
                delivery_id = cursor.lastrowid
                if status == "received":
                    apply_inventory_delta(cursor, item_id, inventory_delta(movement_type, quantity))
                connection.commit()
                refresh_system_alerts(cursor, connection)
            log_audit("create", "supplier_delivery", delivery_id, f"Added {movement_type} delivery for {supplier_name}.")
            flash("Delivery record added.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Could not add delivery record.", "danger")
        return redirect(url_for("main.tracking"))
    
    
    @main.route("/tracking/edit/<int:delivery_id>", methods=["POST"])
    @role_required("admin", "manager")
    def tracking_edit(delivery_id):
        try:
            supplier_name = request.form.get("supplier_name", "").strip()
            movement_type = request.form.get("movement_type", "inbound")
            item_id = int_form("item_id", "Item", 1)
            quantity = decimal_form("quantity", "Quantity", 0.01)
            expected_date = date_form("expected_date", "Expected date")
            received_date = date_form("received_date", "Received date")
            status = request.form.get("status", "pending")
            if not supplier_name or status not in DELIVERY_STATUSES or movement_type not in MOVEMENT_TYPES:
                raise ValueError("Please provide valid delivery details.")
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    "SELECT movement_type, item_id, quantity, status FROM supplier_deliveries WHERE delivery_id = %s",
                    (delivery_id,),
                )
                old = cursor.fetchone()
                if old is None:
                    raise ValueError("Delivery record was not found.")
                if old["status"] == "received":
                    if old["item_id"] is not None and old["quantity"] is not None:
                        apply_inventory_delta(
                            cursor,
                            old["item_id"],
                            -inventory_delta(old["movement_type"], float(old["quantity"])),
                        )
                cursor.execute(
                    """
                    UPDATE supplier_deliveries
                    SET movement_type = %s, supplier_name = %s, item_id = %s, quantity = %s, expected_date = %s,
                        received_date = %s, status = %s
                    WHERE delivery_id = %s
                    """,
                    (movement_type, supplier_name, item_id, quantity, expected_date, received_date, status, delivery_id),
                )
                if status == "received":
                    apply_inventory_delta(cursor, item_id, inventory_delta(movement_type, quantity))
                connection.commit()
                refresh_system_alerts(cursor, connection)
            log_audit("update", "supplier_delivery", delivery_id, "Updated delivery record.")
            flash("Delivery record updated.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Could not update delivery record.", "danger")
        return redirect(url_for("main.tracking"))
    
    
    @main.route("/tracking/delete/<int:delivery_id>", methods=["POST"])
    @role_required("admin", "manager")
    def tracking_delete(delivery_id):
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    "SELECT movement_type, item_id, quantity, status FROM supplier_deliveries WHERE delivery_id = %s",
                    (delivery_id,),
                )
                old = cursor.fetchone()
                if old and old["status"] == "received":
                    apply_inventory_delta(
                        cursor,
                        old["item_id"],
                        -inventory_delta(old["movement_type"], float(old["quantity"])),
                    )
                cursor.execute("DELETE FROM supplier_deliveries WHERE delivery_id = %s", (delivery_id,))
                connection.commit()
            log_audit("delete", "supplier_delivery", delivery_id, "Deleted delivery record.")
            flash("Delivery record deleted.", "success")
        except Error:
            flash("Could not delete delivery record.", "danger")
        return redirect(url_for("main.tracking"))
