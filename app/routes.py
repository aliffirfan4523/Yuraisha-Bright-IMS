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
@login_required
def index():
    return render_template("index.html")


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
        return redirect(url_for("main.index"))

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
