from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db_connection


main = Blueprint("main", __name__)


def login_required(view_function):
    """Redirect visitors to the login page if they are not logged in."""
    @wraps(view_function)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please log in to access the dashboard.", "warning")
            return redirect(url_for("main.login"))

        return view_function(**kwargs)

    return wrapped_view


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/dashboard")
@login_required
def dashboard():
    connection = None
    cursor = None
    
    # Default values
    total_items = 0
    low_stock_count = 0
    deliveries_mtd = 0
    transactions_count = 0
    inbound_tx_count = 0
    outbound_tx_count = 0
    alerts_data = []

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT COALESCE(SUM(quantity), 0) AS total FROM inventory_items")
        total_items = int(cursor.fetchone()["total"])
        
        cursor.execute("SELECT COUNT(*) AS count FROM inventory_items WHERE quantity <= minimum_stock")
        low_stock_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) AS count FROM supplier_deliveries WHERE MONTH(expected_date) = MONTH(CURRENT_DATE) AND YEAR(expected_date) = YEAR(CURRENT_DATE)")
        deliveries_mtd = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) AS count FROM client_transactions")
        transactions_count = cursor.fetchone()["count"]
        
        # Action Center Alerts
        cursor.execute("SELECT * FROM notifications WHERE is_read = FALSE ORDER BY created_at DESC LIMIT 3")
        alerts_data = cursor.fetchall()
        
        # Recent Transactions
        cursor.execute("SELECT * FROM client_transactions ORDER BY transaction_date DESC LIMIT 5")
        recent_txs = cursor.fetchall()
        
    except Error:
        pass
    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()

    return render_template(
        "dashboard.html",
        total_items=f"{total_items:,}",
        low_stock_count=low_stock_count,
        deliveries_mtd=deliveries_mtd,
        transactions_count=f"{transactions_count:,}",
        alerts=alerts_data,
        transactions=recent_txs
    )


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = request.form.get("login_id", "").strip().lower()
        password = request.form.get("password", "")

        if not login_id or not password:
            flash("Please enter your username/email and password.", "danger")
            return redirect(url_for("main.login"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT user_id, full_name, username, email, password_hash, role
                FROM users
                WHERE username = %s OR email = %s
                """,
                (login_id, login_id),
            )
            user = cursor.fetchone()
        except Error:
            flash("Could not connect to the database. Please check your MySQL setup.", "danger")
            return redirect(url_for("main.login"))
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username/email or password.", "danger")
            return redirect(url_for("main.login"))

        session.clear()
        session["user_id"] = user["user_id"]
        session["user_name"] = user["full_name"]
        session["username"] = user["username"]
        session["user_role"] = user["role"]

        flash("Login successful.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not username or not email or not role or not password or not confirm_password:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("main.register"))

        if role not in ["admin", "manager"]:
            flash("Please select a valid user role.", "danger")
            return redirect(url_for("main.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("main.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("main.register"))

        password_hash = generate_password_hash(password)

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT user_id, username, email
                FROM users
                WHERE username = %s OR email = %s
                """,
                (username, email),
            )
            existing_user = cursor.fetchone()

            if existing_user:
                flash("An account with this username or email already exists.", "warning")
                return redirect(url_for("main.register"))

            cursor.execute(
                """
                INSERT INTO users (full_name, username, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (full_name, username, email, password_hash, role),
            )
            connection.commit()
        except Error:
            flash("Could not save the account. Please check your MySQL setup.", "danger")
            return redirect(url_for("main.register"))
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")


@main.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))

@main.route("/inventory")
@login_required
def inventory():
    connection = None
    cursor = None
    items = []
    
    # Get filters
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM inventory_items WHERE 1=1"
        params = []
        
        if search:
            query += " AND (item_name LIKE %s OR item_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
            
        if category and category != 'All Categories':
            # Map frontend label to enum
            cat_map = {'Raw Materials': 'plastic', 'Components': 'box', 'Cooking Oil': 'cooking_oil'}
            if category in cat_map:
                query += " AND category = %s"
                params.append(cat_map[category])
            
        if status and status != 'All Statuses':
            if status == 'In Stock':
                query += " AND quantity > 50"
            elif status == 'Low Stock':
                query += " AND quantity > 0 AND quantity <= 50"
            elif status == 'Out of Stock':
                query += " AND quantity = 0"
                
        query += " ORDER BY item_id DESC"
        
        cursor.execute(query, params)
        items = cursor.fetchall()
    except Error as e:
        flash(f"Error loading inventory: {e}", "danger")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return render_template("inventory.html", items=items, current_search=search, current_category=category, current_status=status)

@main.route("/inventory/add", methods=["POST"])
@login_required
def inventory_add():
    item_name = request.form.get("item_name")
    category = request.form.get("category")
    quantity = request.form.get("quantity", 0)
    unit = request.form.get("unit", "Units")
    min_stock = request.form.get("minimum_stock", 0)
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO inventory_items (item_name, category, quantity, unit, minimum_stock) VALUES (%s, %s, %s, %s, %s)",
            (item_name, category, quantity, unit, min_stock)
        )
        connection.commit()
        flash("Item added successfully.", "success")
    except Error as e:
        flash(f"Error adding item: {e}", "danger")
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'connection' in locals() and connection and connection.is_connected(): connection.close()
        
    return redirect(url_for('main.inventory'))

@main.route("/inventory/edit/<int:item_id>", methods=["POST"])
@login_required
def inventory_edit(item_id):
    item_name = request.form.get("item_name")
    category = request.form.get("category")
    quantity = request.form.get("quantity", 0)
    unit = request.form.get("unit", "Units")
    min_stock = request.form.get("minimum_stock", 0)
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE inventory_items SET item_name=%s, category=%s, quantity=%s, unit=%s, minimum_stock=%s WHERE item_id=%s",
            (item_name, category, quantity, unit, min_stock, item_id)
        )
        connection.commit()
        flash("Item updated successfully.", "success")
    except Error as e:
        flash(f"Error updating item: {e}", "danger")
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'connection' in locals() and connection and connection.is_connected(): connection.close()
        
    return redirect(url_for('main.inventory'))

@main.route("/inventory/quick_update/<int:item_id>", methods=["POST"])
@login_required
def inventory_quick_update(item_id):
    quantity = request.form.get("quantity", 0)
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE inventory_items SET quantity=%s WHERE item_id=%s",
            (quantity, item_id)
        )
        connection.commit()
        flash("Quantity updated successfully.", "success")
    except Error as e:
        flash(f"Error updating quantity: {e}", "danger")
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'connection' in locals() and connection and connection.is_connected(): connection.close()
        
    return redirect(url_for('main.inventory'))

@main.route("/inventory/delete/<int:item_id>", methods=["POST"])
@login_required
def inventory_delete(item_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM inventory_items WHERE item_id=%s", (item_id,))
        connection.commit()
        flash("Item deleted successfully.", "success")
    except Error as e:
        flash(f"Error deleting item: {e}", "danger")
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'connection' in locals() and connection and connection.is_connected(): connection.close()
        
    return redirect(url_for('main.inventory'))


@main.route("/usage", methods=["GET", "POST"])
@login_required
def usage():
    connection = None
    cursor = None
    oil = {"quantity": 0, "quantity_str": "0"}
    plastic = {"quantity": 0, "quantity_str": "0"}
    
    estimated_output = 0
    remaining_oil = 0
    remaining_plastic = 0
    calculated = False
    limiting_factor = "None"
    oil_ratio = 0.5
    plastic_ratio = 0.1

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get current oil
        cursor.execute("SELECT quantity FROM inventory_items WHERE category = 'cooking_oil' LIMIT 1")
        row = cursor.fetchone()
        if row: 
            oil["quantity"] = float(row["quantity"])
            oil["quantity_str"] = f"{oil['quantity']:,.0f}"
            
        # Get current plastic
        cursor.execute("SELECT quantity FROM inventory_items WHERE category = 'plastic' LIMIT 1")
        row = cursor.fetchone()
        if row: 
            plastic["quantity"] = float(row["quantity"])
            plastic["quantity_str"] = f"{plastic['quantity']:,.0f}"

        if request.method == "POST":
            input_oil = float(request.form.get("available_oil", 0))
            input_plastic = float(request.form.get("available_plastic", 0))
            
            # Calculations
            possible_by_oil = int(input_oil / oil_ratio) if oil_ratio > 0 else 0
            possible_by_plastic = int(input_plastic / plastic_ratio) if plastic_ratio > 0 else 0
            
            estimated_output = min(possible_by_oil, possible_by_plastic)
            remaining_oil = input_oil - (estimated_output * oil_ratio)
            remaining_plastic = input_plastic - (estimated_output * plastic_ratio)
            limiting_factor = "Plastic" if possible_by_plastic < possible_by_oil else "Oil"
            calculated = True
            
            # Save calculation
            cursor.execute("""
                INSERT INTO usage_calculations (available_oil, available_plastic, boxes_can_produce, remaining_oil, remaining_plastic, calculated_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (input_oil, input_plastic, estimated_output, remaining_oil, remaining_plastic, session.get("user_id")))
            connection.commit()
            
    except Error as e:
        flash(f"Error calculating usage: {e}", "danger")
    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()

    return render_template(
        "usage.html", 
        oil=oil, 
        plastic=plastic,
        calculated=calculated,
        estimated_output=f"{estimated_output:,}",
        remaining_oil=remaining_oil,
        remaining_plastic=remaining_plastic,
        limiting_factor=limiting_factor
    )


@main.route("/alerts")
@login_required
def alerts():
    connection = None
    cursor = None
    alerts_data = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notifications ORDER BY created_at DESC")
        alerts_data = cursor.fetchall()
    except Error:
        pass
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
            
    return render_template("alerts.html", alerts=alerts_data)


@main.route("/tracking")
@login_required
def tracking():
    connection = None
    cursor = None
    deliveries = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.*, i.item_name 
            FROM supplier_deliveries d
            LEFT JOIN inventory_items i ON d.item_id = i.item_id
            ORDER BY expected_date DESC
        """)
        deliveries = cursor.fetchall()
    except Error:
        pass
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
            
    return render_template("tracking.html", deliveries=deliveries)


@main.route("/transactions")
@login_required
def transactions():
    connection = None
    cursor = None
    txs = []
    monthly_revenue = 0
    pending_payments = 0
    pending_invoices = 0
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Monthly Revenue (current month completed)
        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM client_transactions WHERE payment_status = 'completed' AND MONTH(transaction_date) = MONTH(CURRENT_DATE) AND YEAR(transaction_date) = YEAR(CURRENT_DATE)")
        monthly_revenue = float(cursor.fetchone()["total"])
        
        # Pending Payments
        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count FROM client_transactions WHERE payment_status = 'pending'")
        res = cursor.fetchone()
        pending_payments = float(res["total"])
        pending_invoices = int(res["count"])
        
        # Recent transactions
        cursor.execute("SELECT * FROM client_transactions ORDER BY transaction_date DESC")
        txs = cursor.fetchall()
    except Error:
        pass
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
            
    return render_template(
        "transactions.html", 
        transactions=txs,
        monthly_revenue=f"{monthly_revenue:,.2f}",
        pending_payments=f"{pending_payments:,.2f}",
        pending_invoices=pending_invoices
    )


@main.route("/reports")
@login_required
def reports():
    # We can pass dummy data or do aggregations for the reports page if needed.
    return render_template("reports.html")
