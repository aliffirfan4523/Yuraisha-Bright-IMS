from datetime import date, datetime, timedelta
from flask import flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

from app.route_support import *

def register_routes(main):
    @main.route("/alerts")
    @login_required
    def alerts():
        alerts_data = []
        alert_type = request.args.get("type", "")
        try:
            with db_cursor() as (connection, cursor):
                all_alerts = get_dynamic_alerts(cursor)
                if alert_type in {"low_stock", "delayed_delivery"}:
                    alerts_data = [a for a in all_alerts if a["type"] == alert_type]
                else:
                    alerts_data = all_alerts
        except Error:
            flash("Could not load alerts.", "danger")
        return render_template("alerts.html", alerts=alerts_data, current_type=alert_type)
    
    @main.route("/alerts/mark-read/<notification_id>", methods=["POST"])
    @login_required
    def alert_mark_read(notification_id):
        flash("Alerts are dynamic and will disappear once resolved.", "info")
        return redirect(url_for("main.alerts"))
    
    @main.route("/alerts/mark-all-read", methods=["POST"])
    @login_required
    def alerts_mark_all_read():
        flash("Alerts are dynamic and will disappear once resolved.", "info")
        return redirect(url_for("main.alerts"))
