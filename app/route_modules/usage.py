from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def register_routes(main):
    @main.route("/usage", methods=["GET", "POST"])
    @login_required
    def usage():
        oil = {"quantity": 0, "quantity_str": "0"}
        plastic = {"quantity": 0, "quantity_str": "0"}
        history = []
        result = None
        selected_box_size = request.form.get("box_size", "1")
        selected_ratio = BOX_RATIOS.get(selected_box_size, BOX_RATIOS["1"])
    
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) AS quantity FROM inventory_items WHERE category = 'cooking_oil'")
                oil["quantity"] = float(cursor.fetchone()["quantity"])
                oil["quantity_str"] = f"{oil['quantity']:,.0f}"
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) AS quantity FROM inventory_items WHERE category = 'plastic'")
                plastic["quantity"] = float(cursor.fetchone()["quantity"])
                plastic["quantity_str"] = f"{plastic['quantity']:,.0f}"
                if request.method == "POST":
                    input_oil = decimal_form("available_oil", "Available oil")
                    input_plastic = decimal_form("available_plastic", "Available plastic")
                    if selected_box_size not in BOX_RATIOS:
                        raise ValueError("Please select a valid box ratio.")
                    oil_ratio = selected_ratio["oil_ratio"]
                    plastic_ratio = selected_ratio["plastic_ratio"]
                    possible_by_oil = int(input_oil / oil_ratio)
                    possible_by_plastic = int(input_plastic / plastic_ratio)
                    estimated_output = min(possible_by_oil, possible_by_plastic)
                    remaining_oil = max(input_oil - (estimated_output * oil_ratio), 0)
                    remaining_plastic = max(input_plastic - (estimated_output * plastic_ratio), 0)
                    limiting_factor = "Plastic" if possible_by_plastic < possible_by_oil else "Oil"
                    if possible_by_oil == possible_by_plastic:
                        limiting_factor = "Balanced"
                    cursor.execute(
                        """
                        INSERT INTO usage_calculations
                        (box_size_kg, oil_ratio, plastic_ratio, available_oil, available_plastic,
                         boxes_can_produce, remaining_oil, remaining_plastic, calculated_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            float(selected_box_size),
                            oil_ratio,
                            plastic_ratio,
                            input_oil,
                            input_plastic,
                            estimated_output,
                            remaining_oil,
                            remaining_plastic,
                            current_user_id(),
                        ),
                    )
                    connection.commit()
                    log_audit("calculate", "usage_calculation", cursor.lastrowid, "Production usage calculated.")
                    result = {
                        "estimated_output": f"{estimated_output:,}",
                        "remaining_oil": remaining_oil,
                        "remaining_plastic": remaining_plastic,
                        "limiting_factor": limiting_factor,
                        "input_oil": input_oil,
                        "input_plastic": input_plastic,
                        "box_label": selected_ratio["label"],
                        "oil_ratio": oil_ratio,
                        "plastic_ratio": plastic_ratio,
                    }
                cursor.execute(
                    """
                    SELECT c.*, u.full_name
                    FROM usage_calculations c
                    LEFT JOIN users u ON c.calculated_by = u.user_id
                    ORDER BY calculated_at DESC
                    LIMIT 8
                    """
                )
                history = cursor.fetchall()
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Error calculating usage.", "danger")
    
        return render_template(
            "usage.html",
            oil=oil,
            plastic=plastic,
            result=result,
            history=history,
            box_ratios=BOX_RATIOS,
            selected_box_size=selected_box_size,
            selected_ratio=selected_ratio,
        )
    
    
    @main.route("/usage/history")
    @login_required
    def usage_history():
        return redirect(url_for("main.usage"))
