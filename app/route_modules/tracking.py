from datetime import date, datetime, timedelta
import csv
import io

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

from app.route_support import *

def register_routes(main):
    @main.route("/tracking")
    @login_required
    def tracking():
        deliveries = []
        materials = []
        suppliers = []
        status = request.args.get("status", "")
        movement_type = request.args.get("movement_type", "")
        search = request.args.get("q", "").strip()
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute("SELECT material_id, material_name FROM tbl_material ORDER BY material_name")
                materials = cursor.fetchall()
                
                cursor.execute("SELECT supplier_id, supplier_name FROM tbl_supplier ORDER BY supplier_name")
                suppliers = cursor.fetchall()

                # Fetch Inbound Deliveries
                if movement_type in ["", "inbound"]:
                    query = """
                        SELECT d.delivery_id as id, 'inbound' as movement_type, m.material_name, s.supplier_name as party_name, u.employee_name,
                               d.tracking_number, d.quantity_delivered as quantity, d.expected_arrival as expected_date, d.actual_arrival as actual_date, d.shipping_status as status,
                               d.supplier_id, d.material_id
                        FROM tbl_delivery_log d
                        LEFT JOIN tbl_material m ON d.material_id = m.material_id
                        LEFT JOIN tbl_supplier s ON d.supplier_id = s.supplier_id
                        LEFT JOIN tbl_user u ON d.user_id = u.user_id
                        WHERE 1=1
                    """
                    params = []
                    if status in SHIPPING_STATUSES:
                        query += " AND d.shipping_status = %s"
                        params.append(status)
                    if search:
                        query += " AND (s.supplier_name LIKE %s OR m.material_name LIKE %s OR d.tracking_number LIKE %s)"
                        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                    cursor.execute(query, params)
                    deliveries.extend(cursor.fetchall())

                # Fetch Outbound Client Transactions (Sync Through)
                if movement_type in ["", "outbound"]:
                    query = """
                        SELECT t.transaction_id as id, 'outbound' as movement_type, 'Finished 17kg Boxes' as material_name, t.client_name as party_name, u.employee_name,
                               NULL as tracking_number, t.quantity_sold as quantity, t.transaction_date as expected_date, t.transaction_date as actual_date, 
                               CASE WHEN t.transaction_status = 'completed' THEN 'received' WHEN t.transaction_status = 'pending' THEN 'pending' ELSE 'delayed' END as status,
                               NULL as supplier_id, NULL as material_id
                        FROM tbl_client_transaction t
                        LEFT JOIN tbl_user u ON t.user_id = u.user_id
                        WHERE 1=1
                    """
                    params = []
                    if status == "pending":
                        query += " AND t.transaction_status = 'pending'"
                    elif status == "received":
                        query += " AND t.transaction_status = 'completed'"
                    elif status == "delayed":
                        query += " AND t.transaction_status = 'failed'"
                        
                    if search:
                        query += " AND t.client_name LIKE %s"
                        params.append(f"%{search}%")
                    cursor.execute(query, params)
                    deliveries.extend(cursor.fetchall())
                
                # Sort the combined list by expected date descending
                def get_sort_key(x):
                    val = x['expected_date']
                    if val is None:
                        return date.min
                    if isinstance(val, datetime):
                        return val.date()
                    return val
                deliveries.sort(key=get_sort_key, reverse=True)

        except Error:
            flash("Could not load delivery tracking.", "danger")
            
        return render_template(
            "tracking.html",
            deliveries=deliveries,
            materials=materials,
            suppliers=suppliers,
            current_status=status,
            current_movement_type=movement_type,
            current_search=search,
        )
    
    @main.route("/tracking/add", methods=["POST"])
    @role_required("admin", "manager")
    def tracking_add():
        try:
            supplier_id = int_form("supplier_id", "Supplier")
            material_id = int_form("material_id", "Material")
            tracking_number = request.form.get("tracking_number", "").strip() or None
            quantity_delivered = int_form("quantity_delivered", "Quantity")
            expected_arrival = request.form.get("expected_arrival") or None
            actual_arrival = request.form.get("actual_arrival") or None
            status = request.form.get("shipping_status", "pending")
            
            if status not in SHIPPING_STATUSES:
                raise ValueError("Invalid shipping status.")
                
            if status == "received" and not actual_arrival:
                actual_arrival = date.today().strftime('%Y-%m-%d')
                
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    """
                    INSERT INTO tbl_delivery_log (
                        supplier_id, material_id, user_id, tracking_number,
                        quantity_delivered, expected_arrival, actual_arrival, shipping_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (supplier_id, material_id, current_user_id(), tracking_number,
                     quantity_delivered, expected_arrival, actual_arrival, status)
                )
                delivery_id = cursor.lastrowid
                
                if status == "received":
                    apply_material_delta(cursor, material_id, quantity_delivered)
                    
                connection.commit()
            
            log_audit("create", "delivery_log", delivery_id, "Added new delivery tracking.")
            flash("Delivery tracking added successfully.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Could not add delivery tracking.", "danger")
        return redirect(url_for("main.tracking"))
    
    @main.route("/tracking/edit/<int:delivery_id>", methods=["POST"])
    @role_required("admin", "manager")
    def tracking_edit(delivery_id):
        try:
            supplier_id = int_form("supplier_id", "Supplier")
            material_id = int_form("material_id", "Material")
            tracking_number = request.form.get("tracking_number", "").strip() or None
            quantity_delivered = int_form("quantity_delivered", "Quantity")
            expected_arrival = request.form.get("expected_arrival") or None
            actual_arrival = request.form.get("actual_arrival") or None
            new_status = request.form.get("shipping_status", "pending")
            
            if new_status not in SHIPPING_STATUSES:
                raise ValueError("Invalid shipping status.")
                
            if new_status == "received" and not actual_arrival:
                actual_arrival = date.today().strftime('%Y-%m-%d')
                
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    "SELECT material_id, quantity_delivered, shipping_status FROM tbl_delivery_log WHERE delivery_id = %s",
                    (delivery_id,)
                )
                old_record = cursor.fetchone()
                if not old_record:
                    raise ValueError("Delivery record not found.")
                    
                if old_record["shipping_status"] == "received":
                    apply_material_delta(cursor, old_record["material_id"], -old_record["quantity_delivered"])
                    
                cursor.execute(
                    """
                    UPDATE tbl_delivery_log
                    SET supplier_id = %s, material_id = %s, tracking_number = %s,
                        quantity_delivered = %s, expected_arrival = %s, actual_arrival = %s,
                        shipping_status = %s
                    WHERE delivery_id = %s
                    """,
                    (supplier_id, material_id, tracking_number, quantity_delivered,
                     expected_arrival, actual_arrival, new_status, delivery_id)
                )
                
                if new_status == "received":
                    apply_material_delta(cursor, material_id, quantity_delivered)
                    
                connection.commit()
            
            log_audit("update", "delivery_log", delivery_id, "Updated delivery tracking.")
            flash("Delivery tracking updated.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Could not update delivery tracking.", "danger")
        return redirect(url_for("main.tracking"))
    
    @main.route("/tracking/delete/<int:delivery_id>", methods=["POST"])
    @role_required("admin", "manager")
    def tracking_delete(delivery_id):
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    "SELECT material_id, quantity_delivered, shipping_status FROM tbl_delivery_log WHERE delivery_id = %s",
                    (delivery_id,)
                )
                old_record = cursor.fetchone()
                if not old_record:
                    raise ValueError("Delivery record not found.")
                    
                if old_record["shipping_status"] == "received":
                    apply_material_delta(cursor, old_record["material_id"], -old_record["quantity_delivered"])
                    
                cursor.execute("DELETE FROM tbl_delivery_log WHERE delivery_id = %s", (delivery_id,))
                connection.commit()
                
            log_audit("delete", "delivery_log", delivery_id, "Deleted delivery tracking record.")
            flash("Delivery tracking record deleted.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Could not delete delivery tracking record.", "danger")
        return redirect(url_for("main.tracking"))
