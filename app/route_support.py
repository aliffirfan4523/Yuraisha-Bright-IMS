import hmac
import re
import secrets
import logging
from contextlib import contextmanager
from datetime import datetime, date
from functools import wraps

from flask import abort, flash, request, session, url_for, redirect
from mysql.connector import Error

from app.db import get_db_connection

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

ROLES = {"admin", "manager"}
SHIPPING_STATUSES = {"pending", "received", "delayed"}
TRANSACTION_STATUSES = {"pending", "completed", "failed"}

LOGIN_LOCK_LIMIT = 5
LOGIN_LOCK_MINUTES = 15

@contextmanager
def db_cursor(dictionary=True):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=dictionary)
        yield connection, cursor
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please log in to access the system.", "warning")
            return redirect(url_for("main.login"))
        return view_function(**kwargs)
    return wrapped_view

def role_required(*allowed_roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(**kwargs):
            if "user_id" not in session:
                flash("Please log in to access the system.", "warning")
                return redirect(url_for("main.login"))
            if session.get("user_role") not in allowed_roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("main.dashboard"))
            return view_function(**kwargs)
        return wrapped_view
    return decorator

def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token

def protect_post_requests():
    if request.method != "POST":
        return
    expected = session.get("_csrf_token")
    supplied = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        abort(400, description="Invalid security token.")

def get_dynamic_alerts(cursor):
    alerts = []
    
    # 1. Low stock alerts
    cursor.execute(
        "SELECT material_id, material_name, current_quantity, low_stock_threshold "
        "FROM tbl_material WHERE current_quantity <= low_stock_threshold"
    )
    for mat in cursor.fetchall():
        alerts.append({
            "id": f"mat-{mat['material_id']}",
            "title": f"Low Stock: {mat['material_name']}",
            "message": f"{mat['material_name']} is at {mat['current_quantity']} (threshold: {mat['low_stock_threshold']}).",
            "type": "low_stock",
            "created_at": datetime.now()
        })
        
    # 2. Delayed deliveries
    cursor.execute(
        "SELECT d.delivery_id, d.expected_arrival, s.supplier_name "
        "FROM tbl_delivery_log d "
        "LEFT JOIN tbl_supplier s ON d.supplier_id = s.supplier_id "
        "WHERE d.shipping_status = 'pending' AND d.expected_arrival < CURDATE()"
    )
    for d in cursor.fetchall():
        date_str = d['expected_arrival'].strftime('%Y-%m-%d') if d['expected_arrival'] else 'Unknown'
        alerts.append({
            "id": f"del-{d['delivery_id']}",
            "title": f"Delayed Delivery: TRK-{d['delivery_id']}",
            "message": f"Delivery from {d['supplier_name'] or 'Unknown'} was expected on {date_str} and is now delayed.",
            "type": "delayed_delivery",
            "created_at": datetime.now()
        })
        
    return alerts

def inject_global_values():
    alerts = []
    if session.get("user_id"):
        try:
            with db_cursor() as (_, cursor):
                alerts = get_dynamic_alerts(cursor)
        except Error:
            pass
            
    latest_alert = alerts[0] if alerts else None
    
    return {
        "csrf_token": csrf_token,
        "unread_alerts_count": len(alerts),
        "latest_unread_alert": latest_alert,
    }

def current_user_id():
    return session.get("user_id")

def is_valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must include letters and numbers."
    return None

def decimal_form(name, label, minimum=0):
    raw = request.form.get(name, "").strip()
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{label} must be a valid number.")
    if value < minimum:
        raise ValueError(f"{label} cannot be less than {minimum}.")
    return value

def int_form(name, label, minimum=0):
    value = decimal_form(name, label, minimum)
    if int(value) != value:
        raise ValueError(f"{label} must be a whole number.")
    return int(value)

def date_form(name, label, required=False):
    raw = request.form.get(name, "").strip()
    if not raw and not required:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"{label} must use YYYY-MM-DD format.")

def log_audit(action, entity_type, entity_id=None, details=None):
    if not current_user_id():
        return
    logging.info(f"User {current_user_id()} performed '{action}' on {entity_type} {entity_id or ''}: {details}")

def apply_material_delta(cursor, material_id, delta):
    cursor.execute("SELECT current_quantity FROM tbl_material WHERE material_id = %s", (material_id,))
    mat = cursor.fetchone()
    if mat is None:
        raise ValueError("Selected material does not exist.")
    new_quantity = float(mat["current_quantity"]) + float(delta)
    if new_quantity < 0:
        raise ValueError("Quantity deduction cannot exceed available stock.")
    cursor.execute("UPDATE tbl_material SET current_quantity = %s WHERE material_id = %s", (new_quantity, material_id))
