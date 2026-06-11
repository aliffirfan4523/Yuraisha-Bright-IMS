from datetime import date, datetime, timedelta
import csv
import io

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

from app.route_support import *

def register_routes(main):
    @main.route("/transactions")
    @login_required
    def transactions():
        txs = []
        monthly_revenue = 0
        pending_payments = 0
        pending_invoices = 0
        status = request.args.get("status", "")
        search = request.args.get("q", "").strip()
        try:
            with db_cursor() as (_, cursor):
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(transaction_amount), 0) AS total
                    FROM tbl_client_transaction
                    WHERE transaction_status = 'completed'
                    AND MONTH(transaction_date) = MONTH(CURRENT_DATE)
                    AND YEAR(transaction_date) = YEAR(CURRENT_DATE)
                    """
                )
                monthly_revenue = float(cursor.fetchone()["total"])
                
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(transaction_amount), 0) AS total, COUNT(*) AS count
                    FROM tbl_client_transaction
                    WHERE transaction_status = 'pending'
                    """
                )
                res = cursor.fetchone()
                pending_payments = float(res["total"])
                pending_invoices = int(res["count"])
                
                query = """
                    SELECT t.*, u.employee_name
                    FROM tbl_client_transaction t
                    LEFT JOIN tbl_user u ON t.user_id = u.user_id
                    WHERE 1=1
                """
                params = []
                if status in TRANSACTION_STATUSES:
                    query += " AND t.transaction_status = %s"
                    params.append(status)
                if search:
                    query += " AND (t.client_name LIKE %s OR u.employee_name LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%"])
                query += " ORDER BY t.transaction_date DESC, t.transaction_id DESC"
                cursor.execute(query, params)
                txs = cursor.fetchall()
        except Error:
            flash("Could not load transactions.", "danger")
            
        return render_template(
            "transactions.html",
            transactions=txs,
            monthly_revenue=f"{monthly_revenue:,.2f}",
            pending_payments=f"{pending_payments:,.2f}",
            pending_invoices=pending_invoices,
            current_status=status,
            current_search=search,
        )
    
    @main.route("/transactions/add", methods=["POST"])
    @role_required("admin", "manager")
    def transaction_add():
        return save_transaction()
    
    @main.route("/transactions/edit/<int:transaction_id>", methods=["POST"])
    @role_required("admin", "manager")
    def transaction_edit(transaction_id):
        return save_transaction(transaction_id)
    
    def apply_transaction_materials(cursor, quantity_sold, multiplier=1):
        oil_used = quantity_sold * 17.0
        plastic_used = quantity_sold * 17
        boxes_used = quantity_sold
        
        # Cooking Oil = 1
        # 17kg Empty Boxes = 2
        # 1kg Plastic Packs = 3
        # Ensure we look them up by name to be safe
        cursor.execute("SELECT material_id FROM tbl_material WHERE material_name = 'Cooking Oil'")
        oil = cursor.fetchone()
        if oil: apply_material_delta(cursor, oil['material_id'], -oil_used * multiplier)
        
        cursor.execute("SELECT material_id FROM tbl_material WHERE material_name = '17kg Empty Boxes'")
        box = cursor.fetchone()
        if box: apply_material_delta(cursor, box['material_id'], -boxes_used * multiplier)
        
        cursor.execute("SELECT material_id FROM tbl_material WHERE material_name = '1kg Plastic Packs'")
        plastic = cursor.fetchone()
        if plastic: apply_material_delta(cursor, plastic['material_id'], -plastic_used * multiplier)

    def save_transaction(transaction_id=None):
        try:
            client_name = request.form.get("client_name", "").strip()
            quantity_sold = int_form("quantity_sold", "Quantity sold")
            amount = decimal_form("transaction_amount", "Transaction Amount")
            status = request.form.get("transaction_status", "completed")
            transaction_date = date_form("transaction_date", "Transaction date", required=True)
            
            if not client_name or status not in TRANSACTION_STATUSES:
                raise ValueError("Please provide valid transaction details.")
                
            oil_used_kg = quantity_sold * 17.0
            plastic_used_units = quantity_sold * 17
            
            with db_cursor() as (connection, cursor):
                if transaction_id:
                    cursor.execute(
                        "SELECT quantity_sold, transaction_status FROM tbl_client_transaction WHERE transaction_id = %s",
                        (transaction_id,),
                    )
                    old = cursor.fetchone()
                    if old is None:
                        raise ValueError("Transaction record was not found.")
                    
                    if old["transaction_status"] == "completed":
                        apply_transaction_materials(cursor, old["quantity_sold"], -1) # Revert old
                        
                    cursor.execute(
                        """
                        UPDATE tbl_client_transaction
                        SET client_name = %s, quantity_sold = %s, oil_used_kg = %s,
                            plastic_used_units = %s, transaction_amount = %s,
                            transaction_status = %s, transaction_date = %s
                        WHERE transaction_id = %s
                        """,
                        (client_name, quantity_sold, oil_used_kg, plastic_used_units,
                         amount, status, transaction_date, transaction_id),
                    )
                    entity_id = transaction_id
                    action = "update"
                    message = "Transaction updated."
                else:
                    cursor.execute(
                        """
                        INSERT INTO tbl_client_transaction
                        (user_id, client_name, quantity_sold, oil_used_kg, plastic_used_units,
                         transaction_amount, transaction_status, transaction_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (current_user_id(), client_name, quantity_sold, oil_used_kg, plastic_used_units,
                         amount, status, transaction_date),
                    )
                    entity_id = cursor.lastrowid
                    action = "create"
                    message = "Transaction added."
                
                if status == "completed":
                    apply_transaction_materials(cursor, quantity_sold, 1) # Apply new
                    
                connection.commit()
            log_audit(action, "client_transaction", entity_id, f"{message} Client: {client_name}.")
            flash(message, "success")
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Could not save transaction.", "danger")
        return redirect(url_for("main.transactions"))
    
    @main.route("/transactions/delete/<int:transaction_id>", methods=["POST"])
    @role_required("admin", "manager")
    def transaction_delete(transaction_id):
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    "SELECT quantity_sold, transaction_status FROM tbl_client_transaction WHERE transaction_id = %s",
                    (transaction_id,),
                )
                old = cursor.fetchone()
                if old and old["transaction_status"] == "completed":
                    apply_transaction_materials(cursor, old["quantity_sold"], -1) # Revert old
                    
                cursor.execute("DELETE FROM tbl_client_transaction WHERE transaction_id = %s", (transaction_id,))
                connection.commit()
            log_audit("delete", "client_transaction", transaction_id, "Deleted client transaction.")
            flash("Transaction deleted.", "success")
        except Error:
            flash("Could not delete transaction.", "danger")
        return redirect(url_for("main.transactions"))
