import hmac
import re
import secrets
from contextlib import contextmanager
from datetime import datetime
from functools import wraps

from flask import abort, flash, request, session, url_for, redirect
from mysql.connector import Error

from app.db import get_db_connection


ROLES = {"admin", "manager"}
ITEM_CATEGORIES = {"box", "plastic", "cooking_oil"}
DELIVERY_STATUSES = {"pending", "received", "delayed"}
PAYMENT_STATUSES = {"pending", "completed", "failed"}
REPORT_TYPES = {"inventory", "stock_summary", "supplier", "transaction"}
MOVEMENT_TYPES = {"inbound", "outbound"}
LOGIN_LOCK_LIMIT = 5
LOGIN_LOCK_MINUTES = 15
BOX_RATIOS = {
    "1": {"label": "1kg Box", "oil_ratio": 1.0, "plastic_ratio": 0.10},
    "3": {"label": "3kg Box", "oil_ratio": 3.0, "plastic_ratio": 0.30},
    "5": {"label": "5kg Box", "oil_ratio": 5.0, "plastic_ratio": 0.50},
    "10": {"label": "10kg Box", "oil_ratio": 10.0, "plastic_ratio": 1.00},
}
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


def inject_global_values():
    unread_alerts_count = 0
    if session.get("user_id"):
        try:
            with db_cursor() as (_, cursor):
                cursor.execute("SELECT COUNT(*) AS count FROM notifications WHERE is_read = FALSE")
                unread_alerts_count = cursor.fetchone()["count"]
        except Error:
            unread_alerts_count = 0
    return {"csrf_token": csrf_token, "unread_alerts_count": unread_alerts_count}


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
    try:
        with db_cursor() as (connection, cursor):
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (current_user_id(), action, entity_type, entity_id, details),
            )
            connection.commit()
    except Error:
        pass


def notification_exists(cursor, title, notification_type):
    cursor.execute(
        """
        SELECT notification_id
        FROM notifications
        WHERE title = %s AND type = %s
        LIMIT 1
        """,
        (title, notification_type),
    )
    return cursor.fetchone() is not None


def inventory_delta(movement_type, quantity):
    return quantity if movement_type == "inbound" else -quantity


def apply_inventory_delta(cursor, item_id, delta):
    cursor.execute("SELECT quantity FROM inventory_items WHERE item_id = %s", (item_id,))
    item = cursor.fetchone()
    if item is None:
        raise ValueError("Selected inventory item does not exist.")
    new_quantity = float(item["quantity"]) + float(delta)
    if new_quantity < 0:
        raise ValueError("Outbound quantity cannot exceed available stock.")
    cursor.execute("UPDATE inventory_items SET quantity = %s WHERE item_id = %s", (new_quantity, item_id))


def refresh_system_alerts(cursor, connection):
    cursor.execute(
        """
        SELECT item_id, item_name, quantity, minimum_stock
        FROM inventory_items
        WHERE quantity <= minimum_stock
        """
    )
    for item in cursor.fetchall():
        title = f"Low Stock: {item['item_name']}"
        message = (
            f"{item['item_name']} is at {item['quantity']} and has reached "
            f"the minimum stock level of {item['minimum_stock']}."
        )
        if not notification_exists(cursor, title, "low_stock"):
            cursor.execute(
                """
                INSERT INTO notifications (title, message, type, is_read)
                VALUES (%s, %s, 'low_stock', FALSE)
                """,
                (title, message),
            )

    cursor.execute(
        """
        UPDATE supplier_deliveries
        SET status = 'delayed'
        WHERE status = 'pending' AND expected_date IS NOT NULL AND expected_date < CURRENT_DATE
        """
    )
    cursor.execute(
        """
        SELECT delivery_id, supplier_name, expected_date
        FROM supplier_deliveries
        WHERE status = 'delayed'
        """
    )
    for delivery in cursor.fetchall():
        title = f"Delayed Delivery: TRK-{delivery['delivery_id']}"
        message = (
            f"Delivery from {delivery['supplier_name']} was expected on "
            f"{delivery['expected_date']} and is now delayed."
        )
        if not notification_exists(cursor, title, "delayed_delivery"):
            cursor.execute(
                """
                INSERT INTO notifications (title, message, type, is_read)
                VALUES (%s, %s, 'delayed_delivery', FALSE)
                """,
                (title, message),
            )
    connection.commit()

