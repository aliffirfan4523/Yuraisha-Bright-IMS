from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def register_routes(main):
    def users_count(cursor):
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        return cursor.fetchone()["count"]
    @main.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            login_id = request.form.get("login_id", "").strip().lower()
            password = request.form.get("password", "")
            now = datetime.utcnow()
            lock_until = session.get("login_lock_until")
            if lock_until and datetime.fromisoformat(lock_until) > now:
                flash("Too many failed attempts. Please try again later.", "danger")
                return redirect(url_for("main.login"))
    
            if not login_id or not password:
                flash("Please enter your username/email and password.", "danger")
                return redirect(url_for("main.login"))
    
            try:
                with db_cursor() as (connection, cursor):
                    cursor.execute(
                        """
                        SELECT user_id, full_name, username, email, password_hash, role, is_active
                        FROM users
                        WHERE username = %s OR email = %s
                        """,
                        (login_id, login_id),
                    )
                    user = cursor.fetchone()
                    valid = user is not None and user["is_active"] and check_password_hash(
                        user["password_hash"], password
                    )
                    if not valid:
                        failures = int(session.get("login_failures", 0)) + 1
                        session["login_failures"] = failures
                        if failures >= LOGIN_LOCK_LIMIT:
                            session["login_lock_until"] = (
                                now + timedelta(minutes=LOGIN_LOCK_MINUTES)
                            ).isoformat()
                        flash("Invalid username/email or password.", "danger")
                        return redirect(url_for("main.login"))
    
                    session.clear()
                    session.permanent = bool(request.form.get("remember"))
                    session["user_id"] = user["user_id"]
                    session["user_name"] = user["full_name"]
                    session["username"] = user["username"]
                    session["user_role"] = user["role"]
                    session["_csrf_token"] = secrets.token_urlsafe(32)
                    cursor.execute(
                        "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = %s",
                        (user["user_id"],),
                    )
                    connection.commit()
            except Error:
                flash("Could not connect to the database. Please check your MySQL setup.", "danger")
                return redirect(url_for("main.login"))
    
            log_audit("login", "user", current_user_id(), "User signed in.")
            flash("Login successful.", "success")
            return redirect(url_for("main.dashboard"))
    
        return render_template("login.html")
    
    
    @main.route("/register", methods=["GET", "POST"])
    def register():
        first_account = False
        try:
            with db_cursor() as (_, cursor):
                first_account = users_count(cursor) == 0
        except Error:
            first_account = False
    
        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            username = request.form.get("username", "").strip().lower()
            email = request.form.get("email", "").strip().lower()
            requested_role = request.form.get("role", "manager")
            role = requested_role if first_account or session.get("user_role") == "admin" else "manager"
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
    
            if not full_name or not username or not email or not role or not password or not confirm_password:
                flash("Please fill in all fields.", "danger")
                return redirect(url_for("main.register"))
            if role not in ROLES:
                flash("Please select a valid user role.", "danger")
                return redirect(url_for("main.register"))
            if not is_valid_email(email):
                flash("Please enter a valid email address.", "danger")
                return redirect(url_for("main.register"))
            password_error = validate_password(password)
            if password_error:
                flash(password_error, "danger")
                return redirect(url_for("main.register"))
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("main.register"))
    
            try:
                with db_cursor() as (connection, cursor):
                    cursor.execute(
                        "SELECT user_id FROM users WHERE username = %s OR email = %s",
                        (username, email),
                    )
                    if cursor.fetchone():
                        flash("An account with this username or email already exists.", "warning")
                        return redirect(url_for("main.register"))
                    cursor.execute(
                        """
                        INSERT INTO users (full_name, username, email, password_hash, role, is_active)
                        VALUES (%s, %s, %s, %s, %s, TRUE)
                        """,
                        (full_name, username, email, generate_password_hash(password), role),
                    )
                    connection.commit()
            except Error:
                flash("Could not save the account. Please check your MySQL setup.", "danger")
                return redirect(url_for("main.register"))
    
            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for("main.login"))
    
        return render_template("register.html", first_account=first_account)
    
    
    @main.route("/logout")
    def logout():
        if current_user_id():
            log_audit("logout", "user", current_user_id(), "User signed out.")
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("main.login"))


    @main.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        user = None
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute(
                    """
                    SELECT user_id, full_name, username, email, password_hash, role, last_login_at, created_at
                    FROM users
                    WHERE user_id = %s
                    """,
                    (current_user_id(),),
                )
                user = cursor.fetchone()
                if user is None:
                    session.clear()
                    flash("Please log in again.", "warning")
                    return redirect(url_for("main.login"))

                if request.method == "POST":
                    action = request.form.get("action", "")
                    if action == "update_name":
                        full_name = request.form.get("full_name", "").strip()
                        if not full_name:
                            raise ValueError("Full name is required.")
                        if len(full_name) > 100:
                            raise ValueError("Full name is too long.")
                        cursor.execute(
                            "UPDATE users SET full_name = %s WHERE user_id = %s",
                            (full_name, current_user_id()),
                        )
                        connection.commit()
                        session["user_name"] = full_name
                        log_audit("update_profile", "user", current_user_id(), "Updated profile name.")
                        flash("Profile name updated.", "success")
                        return redirect(url_for("main.profile"))

                    if action == "change_password":
                        current_password = request.form.get("current_password", "")
                        new_password = request.form.get("new_password", "")
                        confirm_password = request.form.get("confirm_password", "")
                        if not check_password_hash(user["password_hash"], current_password):
                            raise ValueError("Current password is incorrect.")
                        password_error = validate_password(new_password)
                        if password_error:
                            raise ValueError(password_error)
                        if new_password != confirm_password:
                            raise ValueError("New passwords do not match.")
                        cursor.execute(
                            "UPDATE users SET password_hash = %s WHERE user_id = %s",
                            (generate_password_hash(new_password), current_user_id()),
                        )
                        connection.commit()
                        log_audit("change_password", "user", current_user_id(), "User changed own password.")
                        flash("Password changed successfully.", "success")
                        return redirect(url_for("main.profile"))

                    raise ValueError("Unknown profile action.")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("main.profile"))
        except Error:
            flash("Could not update profile. Please check your MySQL setup.", "danger")
            return redirect(url_for("main.dashboard"))

        return render_template("profile.html", user=user)
    
