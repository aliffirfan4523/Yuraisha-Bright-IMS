from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def register_routes(main):
    @main.route("/transactions")
    @login_required
    def transactions():
        txs = []
        items = []
        monthly_revenue = 0
        pending_payments = 0
        pending_invoices = 0
        status = request.args.get("status", "")
        movement_type = request.args.get("movement_type", "")
        search = request.args.get("q", "").strip()
        try:
            with db_cursor() as (_, cursor):
                cursor.execute("SELECT item_id, item_name, unit FROM inventory_items ORDER BY item_name")
                items = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) AS total
                    FROM client_transactions
                    WHERE payment_status = 'completed'
                    AND movement_type = 'outbound'
                    AND MONTH(transaction_date) = MONTH(CURRENT_DATE)
                    AND YEAR(transaction_date) = YEAR(CURRENT_DATE)
                    """
                )
                monthly_revenue = float(cursor.fetchone()["total"])
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
                    FROM client_transactions
                    WHERE payment_status = 'pending'
                    """
                )
                res = cursor.fetchone()
                pending_payments = float(res["total"])
                pending_invoices = int(res["count"])
                query = """
                    SELECT t.*, i.item_name
                    FROM client_transactions t
                    LEFT JOIN inventory_items i ON t.item_id = i.item_id
                    WHERE 1=1
                """
                params = []
                if status in PAYMENT_STATUSES:
                    query += " AND t.payment_status = %s"
                    params.append(status)
                if movement_type in MOVEMENT_TYPES:
                    query += " AND t.movement_type = %s"
                    params.append(movement_type)
                if search:
                    query += " AND (t.client_name LIKE %s OR t.notes LIKE %s OR i.item_name LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                query += " ORDER BY t.transaction_date DESC, t.transaction_id DESC"
                cursor.execute(query, params)
                txs = cursor.fetchall()
        except Error:
            flash("Could not load transactions.", "danger")
        return render_template(
            "transactions.html",
            transactions=txs,
            items=items,
            monthly_revenue=f"{monthly_revenue:,.2f}",
            pending_payments=f"{pending_payments:,.2f}",
            pending_invoices=pending_invoices,
            current_status=status,
            current_movement_type=movement_type,
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
    
    
    def save_transaction(transaction_id=None):
        try:
            client_name = request.form.get("client_name", "").strip()
            movement_type = request.form.get("movement_type", "outbound")
            item_id = int_form("item_id", "Inventory item", 1)
            quantity = decimal_form("quantity", "Quantity", 0.01)
            unit = request.form.get("unit", "").strip() or "Units"
            boxes_sold = int(quantity)
            amount = decimal_form("amount", "Amount")
            payment_status = request.form.get("payment_status", "completed")
            transaction_date = date_form("transaction_date", "Transaction date", required=True)
            notes = request.form.get("notes", "").strip()
            if not client_name or payment_status not in PAYMENT_STATUSES or movement_type not in MOVEMENT_TYPES:
                raise ValueError("Please provide valid transaction details.")
            with db_cursor() as (connection, cursor):
                if transaction_id:
                    cursor.execute(
                        "SELECT movement_type, item_id, quantity FROM client_transactions WHERE transaction_id = %s",
                        (transaction_id,),
                    )
                    old = cursor.fetchone()
                    if old is None:
                        raise ValueError("Transaction record was not found.")
                    apply_inventory_delta(
                        cursor,
                        old["item_id"],
                        -inventory_delta(old["movement_type"], float(old["quantity"])),
                    )
                    cursor.execute(
                        """
                        UPDATE client_transactions
                        SET movement_type = %s, item_id = %s, quantity = %s, unit = %s,
                            client_name = %s, boxes_sold = %s, amount = %s,
                            payment_status = %s, transaction_date = %s, notes = %s
                        WHERE transaction_id = %s
                        """,
                        (
                            movement_type,
                            item_id,
                            quantity,
                            unit,
                            client_name,
                            boxes_sold,
                            amount,
                            payment_status,
                            transaction_date,
                            notes,
                            transaction_id,
                        ),
                    )
                    entity_id = transaction_id
                    action = "update"
                    message = "Transaction updated."
                else:
                    cursor.execute(
                        """
                        INSERT INTO client_transactions
                        (movement_type, item_id, quantity, unit, client_name, boxes_sold, amount,
                         payment_status, transaction_date, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            movement_type,
                            item_id,
                            quantity,
                            unit,
                            client_name,
                            boxes_sold,
                            amount,
                            payment_status,
                            transaction_date,
                            notes,
                        ),
                    )
                    entity_id = cursor.lastrowid
                    action = "create"
                    message = "Transaction added."
                apply_inventory_delta(cursor, item_id, inventory_delta(movement_type, quantity))
                connection.commit()
            log_audit(action, "client_transaction", entity_id, f"{message} {movement_type}: {client_name}.")
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
                    "SELECT movement_type, item_id, quantity FROM client_transactions WHERE transaction_id = %s",
                    (transaction_id,),
                )
                old = cursor.fetchone()
                if old and old["item_id"] is not None and old["quantity"] is not None:
                    apply_inventory_delta(
                        cursor,
                        old["item_id"],
                        -inventory_delta(old["movement_type"], float(old["quantity"])),
                    )
                cursor.execute("DELETE FROM client_transactions WHERE transaction_id = %s", (transaction_id,))
                connection.commit()
            log_audit("delete", "client_transaction", transaction_id, "Deleted client transaction.")
            flash("Transaction deleted.", "success")
        except Error:
            flash("Could not delete transaction.", "danger")
        return redirect(url_for("main.transactions"))
