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
PACKAGING_CATEGORIES = {
    "box_1kg",
    "box_3kg",
    "box_5kg",
    "box_10kg",
    "plastic_1kg",
    "plastic_10kg",
    "bottle_3kg",
    "bottle_5kg",
}
PACKAGING_INPUT_ORDER = [
    "plastic_1kg",
    "plastic_10kg",
    "bottle_3kg",
    "bottle_5kg",
    "box_1kg",
    "box_3kg",
    "box_5kg",
    "box_10kg",
]
ITEM_CATEGORIES = PACKAGING_CATEGORIES | {"cooking_oil", "finished_goods", "defect"}
RAW_MATERIAL_CATEGORIES = PACKAGING_CATEGORIES | {"cooking_oil"}
SELLABLE_CATEGORIES = {"finished_goods"}
INVENTORY_CATEGORY_LABELS = {
    "box_1kg": "1kg Boxes",
    "box_3kg": "3kg Boxes",
    "box_5kg": "5kg Boxes",
    "box_10kg": "10kg Boxes",
    "plastic_1kg": "1kg Plastic Packs",
    "plastic_10kg": "10kg Plastic Packs",
    "bottle_3kg": "3kg Bottles",
    "bottle_5kg": "5kg Bottles",
    "cooking_oil": "Cooking Oil",
    "finished_goods": "Finished Goods",
    "defect": "Defect Stock",
}
DEFAULT_INVENTORY_CATEGORY_ORDER = PACKAGING_INPUT_ORDER + ["cooking_oil", "finished_goods", "defect"]
DELIVERY_STATUSES = {"pending", "received", "delayed"}
PAYMENT_STATUSES = {"pending", "completed", "failed"}
REPORT_TYPES = {"inventory", "stock_summary", "supplier", "transaction"}
MOVEMENT_TYPES = {"inbound", "outbound"}
LOGIN_LOCK_LIMIT = 5
LOGIN_LOCK_MINUTES = 15
BOX_RATIOS = {
    "1": {
        "label": "1kg Box",
        "box_size_kg": 1,
        "units_per_box": 20,
        "package_category": "plastic_1kg",
        "package_label": "1kg Plastic Packs",
        "box_category": "box_1kg",
        "box_label": "1kg Boxes",
    },
    "3": {
        "label": "3kg Box",
        "box_size_kg": 3,
        "units_per_box": 4,
        "package_category": "bottle_3kg",
        "package_label": "3kg Bottles",
        "box_category": "box_3kg",
        "box_label": "3kg Boxes",
    },
    "5": {
        "label": "5kg Box",
        "box_size_kg": 5,
        "units_per_box": 2,
        "package_category": "bottle_5kg",
        "package_label": "5kg Bottles",
        "box_category": "box_5kg",
        "box_label": "5kg Boxes",
    },
    "10": {
        "label": "10kg Box",
        "box_size_kg": 10,
        "units_per_box": 1,
        "package_category": "plastic_10kg",
        "package_label": "10kg Plastic Packs",
        "box_category": "box_10kg",
        "box_label": "10kg Boxes",
    },
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
    latest_unread_alert = None
    if session.get("user_id"):
        try:
            with db_cursor() as (_, cursor):
                cursor.execute("SELECT COUNT(*) AS count FROM notifications WHERE is_read = FALSE")
                unread_alerts_count = cursor.fetchone()["count"]
                cursor.execute(
                    """
                    SELECT notification_id, title, message, type, created_at
                    FROM notifications
                    WHERE is_read = FALSE
                    ORDER BY created_at DESC, notification_id DESC
                    LIMIT 1
                    """
                )
                alert = cursor.fetchone()
                if alert:
                    created_at = alert["created_at"]
                    latest_unread_alert = {
                        "id": alert["notification_id"],
                        "title": alert["title"],
                        "message": alert["message"],
                        "type": alert["type"],
                        "created_at": created_at.strftime("%b %d, %H:%M") if created_at else "",
                    }
        except Error:
            unread_alerts_count = 0
            latest_unread_alert = None
    return {
        "csrf_token": csrf_token,
        "unread_alerts_count": unread_alerts_count,
        "latest_unread_alert": latest_unread_alert,
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


def category_key_from_label(label):
    key = re.sub(r"[^a-z0-9]+", "_", (label or "").strip().lower())
    key = re.sub(r"_+", "_", key).strip("_")
    if not key:
        raise ValueError("Category name is required.")
    if len(key) > 50:
        raise ValueError("Category name is too long.")
    return key


def category_label_from_key(category_key):
    return INVENTORY_CATEGORY_LABELS.get(category_key, category_key.replace("_", " ").title())


def ensure_inventory_category_support(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_categories (
            category_key VARCHAR(50) PRIMARY KEY,
            category_label VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute("SHOW COLUMNS FROM inventory_items LIKE 'category'")
    category_column = cursor.fetchone()
    if category_column and not str(category_column.get("Type", "")).lower().startswith("varchar"):
        cursor.execute("ALTER TABLE inventory_items MODIFY category VARCHAR(50) NOT NULL")

    for category_key in DEFAULT_INVENTORY_CATEGORY_ORDER:
        cursor.execute(
            """
            INSERT INTO inventory_categories (category_key, category_label)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE category_label = VALUES(category_label)
            """,
            (category_key, category_label_from_key(category_key)),
        )

    cursor.execute(
        """
        INSERT INTO inventory_categories (category_key, category_label)
        SELECT DISTINCT category, REPLACE(category, '_', ' ')
        FROM inventory_items
        WHERE category IS NOT NULL
        ON DUPLICATE KEY UPDATE category_key = category_key
        """
    )


def get_inventory_categories(cursor):
    ensure_inventory_category_support(cursor)
    cursor.execute(
        """
        SELECT category_key, category_label
        FROM inventory_categories
        ORDER BY
            CASE WHEN FIELD(category_key, 'plastic_1kg', 'plastic_10kg', 'bottle_3kg', 'bottle_5kg',
                'box_1kg', 'box_3kg', 'box_5kg', 'box_10kg',
                'cooking_oil', 'finished_goods', 'defect') = 0 THEN 1 ELSE 0 END,
            FIELD(category_key, 'plastic_1kg', 'plastic_10kg', 'bottle_3kg', 'bottle_5kg',
                'box_1kg', 'box_3kg', 'box_5kg', 'box_10kg',
                'cooking_oil', 'finished_goods', 'defect'),
            category_label
        """
    )
    return cursor.fetchall()


def inventory_category_exists(cursor, category_key):
    cursor.execute(
        "SELECT category_key FROM inventory_categories WHERE category_key = %s",
        (category_key,),
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


def apply_inventory_for_tracking_status(cursor, delivery, new_status):
    old_status = delivery["status"]
    if old_status == new_status:
        return False

    delta = inventory_delta(delivery["movement_type"], float(delivery["quantity"]))
    if old_status == "received":
        apply_inventory_delta(cursor, delivery["item_id"], -delta)
        return True
    if new_status == "received":
        apply_inventory_delta(cursor, delivery["item_id"], delta)
        return True
    return False


def get_inventory_item(cursor, item_id):
    cursor.execute("SELECT * FROM inventory_items WHERE item_id = %s", (item_id,))
    item = cursor.fetchone()
    if item is None:
        raise ValueError("Selected inventory item does not exist.")
    return item


def consume_category_stock(cursor, category, required_quantity):
    remaining = float(required_quantity)
    cursor.execute(
        """
        SELECT item_id, quantity
        FROM inventory_items
        WHERE category = %s AND quantity > 0
        ORDER BY updated_at ASC, item_id ASC
        """,
        (category,),
    )
    items = cursor.fetchall()
    available = sum(float(item["quantity"]) for item in items)
    if available < remaining:
        raise ValueError(f"Not enough {category.replace('_', ' ')} stock for production.")

    for item in items:
        if remaining <= 0:
            break
        take = min(float(item["quantity"]), remaining)
        cursor.execute(
            "UPDATE inventory_items SET quantity = quantity - %s WHERE item_id = %s",
            (take, item["item_id"]),
        )
        remaining -= take


def add_or_increment_inventory_item(cursor, item_name, category, quantity, unit, minimum_stock=0):
    cursor.execute(
        """
        SELECT item_id
        FROM inventory_items
        WHERE item_name = %s AND category = %s AND unit = %s
        LIMIT 1
        """,
        (item_name, category, unit),
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            "UPDATE inventory_items SET quantity = quantity + %s WHERE item_id = %s",
            (quantity, existing["item_id"]),
        )
        return existing["item_id"]

    cursor.execute(
        """
        INSERT INTO inventory_items (item_name, category, quantity, unit, minimum_stock)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (item_name, category, quantity, unit, minimum_stock),
    )
    return cursor.lastrowid


def sync_delivery_from_transaction(cursor, transaction_id, movement_type, client_name, item_id, quantity, transaction_date):
    cursor.execute(
        "SELECT delivery_id, status, expected_date, received_date FROM supplier_deliveries WHERE transaction_id = %s",
        (transaction_id,),
    )
    delivery = cursor.fetchone()
    if delivery:
        cursor.execute(
            """
            UPDATE supplier_deliveries
            SET movement_type = %s,
                supplier_name = %s,
                item_id = %s,
                quantity = %s
            WHERE transaction_id = %s
            """,
            (movement_type, client_name, item_id, quantity, transaction_id),
        )
        return delivery["delivery_id"]

    cursor.execute(
        """
        INSERT INTO supplier_deliveries
        (transaction_id, movement_type, supplier_name, item_id, quantity, expected_date, received_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (transaction_id, movement_type, client_name, item_id, quantity, transaction_date, None, "pending"),
    )
    return cursor.lastrowid


def delete_delivery_for_transaction(cursor, transaction_id):
    cursor.execute("DELETE FROM supplier_deliveries WHERE transaction_id = %s", (transaction_id,))


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

