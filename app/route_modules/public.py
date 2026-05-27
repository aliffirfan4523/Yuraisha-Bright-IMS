from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

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
                refresh_system_alerts(cursor, connection)
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) AS total FROM inventory_items")
                totals["total_items"] = float(cursor.fetchone()["total"])
                cursor.execute("SELECT COUNT(*) AS count FROM inventory_items WHERE quantity <= minimum_stock")
                totals["low_stock_count"] = cursor.fetchone()["count"]
                cursor.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM supplier_deliveries
                    WHERE MONTH(expected_date) = MONTH(CURRENT_DATE)
                    AND YEAR(expected_date) = YEAR(CURRENT_DATE)
                    """
                )
                totals["deliveries_mtd"] = cursor.fetchone()["count"]
                cursor.execute("SELECT COUNT(*) AS count FROM client_transactions")
                totals["transactions_count"] = cursor.fetchone()["count"]
                cursor.execute(
                    "SELECT * FROM notifications WHERE is_read = FALSE ORDER BY created_at DESC LIMIT 3"
                )
                alerts_data = cursor.fetchall()
                cursor.execute(
                    "SELECT * FROM client_transactions ORDER BY transaction_date DESC, transaction_id DESC LIMIT 5"
                )
                recent_txs = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT category, COALESCE(SUM(quantity), 0) AS total
                    FROM inventory_items
                    GROUP BY category
                    ORDER BY category
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
