from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def register_routes(main):
    @main.route("/alerts")
    @login_required
    def alerts():
        alerts_data = []
        alert_type = request.args.get("type", "")
        try:
            with db_cursor() as (connection, cursor):
                refresh_system_alerts(cursor, connection)
                query = "SELECT * FROM notifications"
                params = []
                if alert_type in {"low_stock", "delayed_delivery", "general"}:
                    query += " WHERE type = %s"
                    params.append(alert_type)
                query += " ORDER BY is_read ASC, created_at DESC"
                cursor.execute(query, params)
                alerts_data = cursor.fetchall()
        except Error:
            flash("Could not load alerts.", "danger")
        return render_template("alerts.html", alerts=alerts_data, current_type=alert_type)
    
    
    @main.route("/alerts/mark-read/<int:notification_id>", methods=["POST"])
    @login_required
    def alert_mark_read(notification_id):
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute("UPDATE notifications SET is_read = TRUE WHERE notification_id = %s", (notification_id,))
                connection.commit()
            log_audit("mark_read", "notification", notification_id, "Marked alert as read.")
            flash("Alert marked as read.", "success")
        except Error:
            flash("Could not update alert.", "danger")
        return redirect(url_for("main.alerts"))
    
    
    @main.route("/alerts/mark-all-read", methods=["POST"])
    @login_required
    def alerts_mark_all_read():
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute("UPDATE notifications SET is_read = TRUE WHERE is_read = FALSE")
                connection.commit()
            log_audit("mark_all_read", "notification", None, "Marked all alerts as read.")
            flash("All alerts marked as read.", "success")
        except Error:
            flash("Could not update alerts.", "danger")
        return redirect(url_for("main.alerts"))
