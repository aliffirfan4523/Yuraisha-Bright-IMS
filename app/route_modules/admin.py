from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def register_routes(main):
    @main.route("/admin/users", methods=["GET", "POST"])
    @role_required("admin")
    def admin_users():
        if request.method == "POST":
            action = request.form.get("action", "")
            user_id = request.form.get("user_id", "")
            try:
                with db_cursor() as (connection, cursor):
                    if action == "create":
                        full_name = request.form.get("full_name", "").strip()
                        username = request.form.get("username", "").strip().lower()
                        email = request.form.get("email", "").strip().lower()
                        role = request.form.get("role", "")
                        password = request.form.get("password", "")
                        if not full_name or not username or not email or role not in ROLES:
                            raise ValueError("Please provide valid user details.")
                        password_error = validate_password(password)
                        if password_error:
                            raise ValueError(password_error)
                        if not is_valid_email(email):
                            raise ValueError("Please enter a valid email address.")
                        cursor.execute(
                            "SELECT user_id FROM users WHERE username = %s OR email = %s",
                            (username, email),
                        )
                        if cursor.fetchone():
                            raise ValueError("Username or email already exists.")
                        cursor.execute(
                            """
                            INSERT INTO users (full_name, username, email, password_hash, role, is_active)
                            VALUES (%s, %s, %s, %s, %s, TRUE)
                            """,
                            (full_name, username, email, generate_password_hash(password), role),
                        )
                        connection.commit()
                        log_audit("create", "user", cursor.lastrowid, f"Created user {username}.")
                        flash("User account created.", "success")
                    elif action == "update":
                        role = request.form.get("role", "")
                        is_active = bool(request.form.get("is_active"))
                        if role not in ROLES:
                            raise ValueError("Invalid role selected.")
                        cursor.execute(
                            "UPDATE users SET role = %s, is_active = %s WHERE user_id = %s",
                            (role, is_active, user_id),
                        )
                        connection.commit()
                        log_audit("update", "user", user_id, "Updated user permissions.")
                        flash("User permissions updated.", "success")
                    elif action == "reset_password":
                        password = request.form.get("password", "")
                        password_error = validate_password(password)
                        if password_error:
                            raise ValueError(password_error)
                        cursor.execute(
                            "UPDATE users SET password_hash = %s WHERE user_id = %s",
                            (generate_password_hash(password), user_id),
                        )
                        connection.commit()
                        log_audit("reset_password", "user", user_id, "Password reset by admin.")
                        flash("Password reset successfully.", "success")
                    elif action == "delete":
                        if str(current_user_id()) == str(user_id):
                            raise ValueError("You cannot delete your own account.")
                        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
                        connection.commit()
                        log_audit("delete", "user", user_id, "Deleted user account.")
                        flash("User account deleted.", "success")
                    else:
                        raise ValueError("Unknown user action.")
            except ValueError as exc:
                flash(str(exc), "danger")
            except Error:
                flash("User account action could not be completed.", "danger")
            return redirect(url_for("main.admin_users"))
    
        users = []
        audit_logs = []
        try:
            with db_cursor() as (_, cursor):
                cursor.execute(
                    """
                    SELECT user_id, full_name, username, email, role, is_active, created_at, last_login_at
                    FROM users
                    ORDER BY created_at DESC
                    """
                )
                users = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT a.*, u.username
                    FROM audit_logs a
                    LEFT JOIN users u ON a.user_id = u.user_id
                    ORDER BY a.created_at DESC
                    LIMIT 10
                    """
                )
                audit_logs = cursor.fetchall()
        except Error:
            flash("Could not load users.", "danger")
        return render_template("admin_users.html", users=users, audit_logs=audit_logs)
