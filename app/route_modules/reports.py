from datetime import date, datetime, timedelta
import csv
import io

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

from app.route_support import *

REPORT_TYPES = {"inventory", "delivery", "transaction"}

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
            if report_type == "inventory":
                title = "Inventory Report"
                columns = ["ID", "Material Name", "Current Quantity", "Low Stock Threshold", "Last Updated"]
                cursor.execute(
                    """
                    SELECT material_id, material_name, current_quantity, low_stock_threshold, last_updated
                    FROM tbl_material
                    ORDER BY material_name
                    """
                )
                rows = [
                    [
                        row["material_id"],
                        row["material_name"],
                        row["current_quantity"],
                        row["low_stock_threshold"],
                        row["last_updated"],
                    ]
                    for row in cursor.fetchall()
                ]
            elif report_type == "delivery":
                title = "Delivery Log Report"
                columns = ["Delivery ID", "Supplier", "Material", "Quantity", "Expected Arrival", "Actual Arrival", "Status"]
                query = """
                    SELECT d.delivery_id, s.supplier_name, m.material_name, d.quantity_delivered,
                           d.expected_arrival, d.actual_arrival, d.shipping_status
                    FROM tbl_delivery_log d
                    LEFT JOIN tbl_supplier s ON d.supplier_id = s.supplier_id
                    LEFT JOIN tbl_material m ON d.material_id = m.material_id
                    WHERE 1=1
                """
                params = []
                if start:
                    query += " AND d.expected_arrival >= %s"
                    params.append(start)
                if end:
                    query += " AND d.expected_arrival <= %s"
                    params.append(end)
                query += " ORDER BY d.expected_arrival DESC"
                cursor.execute(query, params)
                rows = [
                    [
                        row["delivery_id"],
                        row["supplier_name"],
                        row["material_name"],
                        row["quantity_delivered"],
                        row["expected_arrival"],
                        row["actual_arrival"],
                        row["shipping_status"],
                    ]
                    for row in cursor.fetchall()
                ]
            else:
                title = "Transaction Report"
                columns = [
                    "Transaction ID",
                    "Client Name",
                    "Quantity Sold (Boxes)",
                    "Amount",
                    "Transaction Status",
                    "Transaction Date",
                    "Recorded By"
                ]
                query = """
                    SELECT t.transaction_id, t.client_name, t.quantity_sold, t.transaction_amount,
                           t.transaction_status, t.transaction_date, u.employee_name
                    FROM tbl_client_transaction t
                    LEFT JOIN tbl_user u ON t.user_id = u.user_id
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
                        row["client_name"],
                        row["quantity_sold"],
                        row["transaction_amount"],
                        row["transaction_status"],
                        row["transaction_date"],
                        row["employee_name"],
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
