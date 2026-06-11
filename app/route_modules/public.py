from datetime import date, datetime, timedelta
from flask import flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

from app.route_support import *

def register_routes(main):
    @main.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("main.dashboard"))
        return render_template("index.html")
    
    @main.route("/dashboard")
    @login_required
    def dashboard():
        totals = {
            "total_items": 0,
            "low_stock_count": 0,
            "deliveries_mtd": 0,
            "transactions_count": 0,
            "inventory_value": 0,
        }
        alerts_data = []
        recent_txs = []
        chart_rows = []
    
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute("SELECT COALESCE(SUM(current_quantity), 0) AS total FROM tbl_material")
                totals["total_items"] = float(cursor.fetchone()["total"])
                
                cursor.execute("SELECT COUNT(*) AS count FROM tbl_material WHERE current_quantity <= low_stock_threshold")
                totals["low_stock_count"] = cursor.fetchone()["count"]
                
                cursor.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM tbl_delivery_log
                    WHERE MONTH(expected_arrival) = MONTH(CURRENT_DATE)
                    AND YEAR(expected_arrival) = YEAR(CURRENT_DATE)
                    """
                )
                totals["deliveries_mtd"] = cursor.fetchone()["count"]
                
                cursor.execute("SELECT COUNT(*) AS count FROM tbl_client_transaction")
                totals["transactions_count"] = cursor.fetchone()["count"]
                
                all_alerts = get_dynamic_alerts(cursor)
                alerts_data = all_alerts[:3]
                
                cursor.execute(
                    "SELECT * FROM tbl_client_transaction ORDER BY transaction_date DESC, transaction_id DESC LIMIT 5"
                )
                recent_txs = cursor.fetchall()
                
                cursor.execute(
                    """
                    SELECT material_name AS category, current_quantity AS total
                    FROM tbl_material
                    ORDER BY material_name
                    """
                )
                chart_rows = cursor.fetchall()
        except Error:
            flash("Dashboard data could not be loaded. Please check the database connection.", "danger")
    
        return render_template(
            "dashboard.html",
            total_items=f"{totals['total_items']:,.0f}",
            low_stock_count=totals["low_stock_count"],
            deliveries_mtd=totals["deliveries_mtd"],
            transactions_count=f"{totals['transactions_count']:,}",
            alerts=alerts_data,
            transactions=recent_txs,
            chart_rows=chart_rows,
        )
