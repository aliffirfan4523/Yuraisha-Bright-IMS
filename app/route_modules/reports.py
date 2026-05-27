from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def register_routes(main):
    def report_date_filters():
        report_type = request.args.get("type", "inventory")
        if report_type not in REPORT_TYPES:
            report_type = "inventory"
        start = request.args.get("start", "")
        end = request.args.get("end", "")
        return report_type, start, end
    
    
    def build_report(report_type, start="", end=""):
        rows = []
        columns = []
        title = ""
        with db_cursor() as (connection, cursor):
            refresh_system_alerts(cursor, connection)
            if report_type == "inventory":
                title = "Inventory Report"
                columns = ["ID", "Item", "Category", "Quantity", "Unit", "Minimum Stock", "Updated"]
                cursor.execute(
                    """
                    SELECT item_id, item_name, category, quantity, unit, minimum_stock, updated_at
                    FROM inventory_items
                    ORDER BY category, item_name
                    """
                )
                rows = [
                    [
                        row["item_id"],
                        row["item_name"],
                        row["category"],
                        row["quantity"],
                        row["unit"],
                        row["minimum_stock"],
                        row["updated_at"],
                    ]
                    for row in cursor.fetchall()
                ]
            elif report_type == "stock_summary":
                title = "Stock Summary"
                columns = ["Category", "Total Quantity", "Low Stock Items", "Items"]
                cursor.execute(
                    """
                    SELECT category, COALESCE(SUM(quantity), 0) AS total_quantity,
                           SUM(CASE WHEN quantity <= minimum_stock THEN 1 ELSE 0 END) AS low_stock_items,
                           COUNT(*) AS items
                    FROM inventory_items
                    GROUP BY category
                    ORDER BY category
                    """
                )
                rows = [
                    [row["category"], row["total_quantity"], row["low_stock_items"], row["items"]]
                    for row in cursor.fetchall()
                ]
            elif report_type == "supplier":
                title = "Supplier Report"
                columns = ["Delivery ID", "Type", "Supplier / Customer", "Item", "Quantity", "Expected", "Received", "Status"]
                query = """
                    SELECT d.delivery_id, d.movement_type, d.supplier_name, i.item_name, d.quantity,
                           d.expected_date, d.received_date, d.status
                    FROM supplier_deliveries d
                    LEFT JOIN inventory_items i ON d.item_id = i.item_id
                    WHERE 1=1
                """
                params = []
                if start:
                    query += " AND d.expected_date >= %s"
                    params.append(start)
                if end:
                    query += " AND d.expected_date <= %s"
                    params.append(end)
                query += " ORDER BY d.expected_date DESC"
                cursor.execute(query, params)
                rows = [
                    [
                        row["delivery_id"],
                        row["movement_type"],
                        row["supplier_name"],
                        row["item_name"],
                        row["quantity"],
                        row["expected_date"],
                        row["received_date"],
                        row["status"],
                    ]
                    for row in cursor.fetchall()
                ]
            else:
                title = "Transaction Report"
                columns = [
                    "Transaction ID",
                    "Type",
                    "Supplier / Customer",
                    "Item",
                    "Quantity",
                    "Amount",
                    "Payment Status",
                    "Date",
                    "Notes",
                ]
                query = """
                    SELECT t.*, i.item_name
                    FROM client_transactions t
                    LEFT JOIN inventory_items i ON t.item_id = i.item_id
                    WHERE 1=1
                """
                params = []
                if start:
                    query += " AND t.transaction_date >= %s"
                    params.append(start)
                if end:
                    query += " AND t.transaction_date <= %s"
                    params.append(end)
                query += " ORDER BY t.transaction_date DESC"
                cursor.execute(query, params)
                rows = [
                    [
                        row["transaction_id"],
                        row["movement_type"],
                        row["client_name"],
                        row["item_name"],
                        f"{row['quantity']} {row['unit']}",
                        row["amount"],
                        row["payment_status"],
                        row["transaction_date"],
                        row["notes"],
                    ]
                    for row in cursor.fetchall()
                ]
        return title, columns, rows
    
    
    @main.route("/reports")
    @role_required("admin", "manager")
    def reports():
        report_type, start, end = report_date_filters()
        title = "Report"
        columns = []
        rows = []
        try:
            title, columns, rows = build_report(report_type, start, end)
        except Error:
            flash("Could not generate report.", "danger")
        return render_template(
            "reports.html",
            report_type=report_type,
            report_title=title,
            columns=columns,
            rows=rows,
            start=start,
            end=end,
        )
    
    
    @main.route("/reports/export.csv")
    @role_required("admin", "manager")
    def reports_export():
        report_type, start, end = report_date_filters()
        try:
            title, columns, rows = build_report(report_type, start, end)
        except Error:
            flash("Could not export report.", "danger")
            return redirect(url_for("main.reports"))
    
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([title])
        writer.writerow(columns)
        writer.writerows(rows)
        filename = f"{report_type}_report_{date.today().isoformat()}.csv"
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
