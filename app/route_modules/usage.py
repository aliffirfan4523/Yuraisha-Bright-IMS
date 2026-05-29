from datetime import date, datetime, timedelta
import csv
import io
import secrets

from flask import Response, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

from app.route_support import *


def ensure_usage_production_log_support(cursor):
    cursor.execute("SHOW COLUMNS FROM usage_calculations LIKE 'record_type'")
    if cursor.fetchone() is None:
        cursor.execute(
            "ALTER TABLE usage_calculations ADD COLUMN record_type VARCHAR(20) NOT NULL DEFAULT 'estimate'"
        )


def register_routes(main):
    @main.route("/usage", methods=["GET", "POST"])
    @login_required
    def usage():
        oil = {"quantity": 0, "quantity_str": "0"}
        packaging_stocks = {
            category: {"label": INVENTORY_CATEGORY_LABELS[category], "quantity": 0, "quantity_str": "0"}
            for category in sorted(PACKAGING_CATEGORIES)
        }
        result = None
        production_readiness = []
        recent_calculations = []
        selected_box_size = request.form.get("box_size", "1")
        selected_ratio = BOX_RATIOS.get(selected_box_size, BOX_RATIOS["1"])
        input_values = {
            "oil": request.form.get("available_oil", "0"),
            "package": request.form.get("available_package", "0"),
            "boxes": request.form.get("available_boxes", "0"),
        }
    
        try:
            with db_cursor() as (connection, cursor):
                ensure_usage_production_log_support(cursor)
                cursor.execute("SELECT COALESCE(SUM(quantity), 0) AS quantity FROM inventory_items WHERE category = 'cooking_oil'")
                oil["quantity"] = float(cursor.fetchone()["quantity"])
                oil["quantity_str"] = f"{oil['quantity']:,.0f}"
                cursor.execute(
                    """
                    SELECT category, COALESCE(SUM(quantity), 0) AS quantity
                    FROM inventory_items
                    WHERE category IN (%s, %s, %s, %s, %s, %s, %s, %s)
                    GROUP BY category
                    """,
                    tuple(sorted(PACKAGING_CATEGORIES)),
                )
                for stock in cursor.fetchall():
                    packaging_stocks[stock["category"]]["quantity"] = float(stock["quantity"])
                    packaging_stocks[stock["category"]]["quantity_str"] = f"{float(stock['quantity']):,.0f}"
                for size, ratio in BOX_RATIOS.items():
                    package_stock = packaging_stocks[ratio["package_category"]]["quantity"]
                    box_stock = packaging_stocks[ratio["box_category"]]["quantity"]
                    oil_needed = ratio["box_size_kg"] * ratio["units_per_box"]
                    possible_by_oil = int(oil["quantity"] / oil_needed) if oil_needed else 0
                    possible_by_package = int(package_stock / ratio["units_per_box"]) if ratio["units_per_box"] else 0
                    possible_by_boxes = int(box_stock)
                    capacity = min(possible_by_oil, possible_by_package, possible_by_boxes)
                    capacity_options = {
                        "Cooking oil": possible_by_oil,
                        ratio["package_label"]: possible_by_package,
                        ratio["box_label"]: possible_by_boxes,
                    }
                    minimum_capacity = min(capacity_options.values())
                    limiting_factor = ", ".join(
                        name for name, available in capacity_options.items() if available == minimum_capacity
                    )
                    if len(set(capacity_options.values())) == 1:
                        limiting_factor = "Balanced"
                    production_readiness.append(
                        {
                            "size": size,
                            "label": ratio["label"],
                            "capacity": capacity,
                            "limiting_factor": limiting_factor,
                            "oil_needed": oil_needed,
                            "package_label": ratio["package_label"],
                            "package_needed": ratio["units_per_box"],
                            "box_label": ratio["box_label"],
                            "status": "Ready" if capacity > 0 else "Blocked",
                        }
                    )
                selected_package_stock = packaging_stocks[selected_ratio["package_category"]]
                selected_box_stock = packaging_stocks[selected_ratio["box_category"]]
                if request.method == "GET":
                    input_values["oil"] = oil["quantity"]
                    input_values["package"] = selected_package_stock["quantity"]
                    input_values["boxes"] = selected_box_stock["quantity"]
                else:
                    input_values["oil"] = request.form.get("available_oil", oil["quantity"])
                    input_values["package"] = request.form.get("available_package", selected_package_stock["quantity"])
                    input_values["boxes"] = request.form.get("available_boxes", selected_box_stock["quantity"])
                if request.method == "POST":
                    action = request.form.get("action", "calculate")
                    input_oil = decimal_form("available_oil", "Available oil")
                    if selected_box_size not in BOX_RATIOS:
                        raise ValueError("Please select a valid box ratio.")
                    units_per_box = selected_ratio["units_per_box"]
                    oil_ratio = selected_ratio["box_size_kg"] * units_per_box
                    package_category = selected_ratio["package_category"]
                    package_label = selected_ratio["package_label"]
                    box_category = selected_ratio["box_category"]
                    box_label = selected_ratio["box_label"]
                    package_ratio = units_per_box
                    input_package = decimal_form("available_package", package_label)
                    input_boxes = decimal_form("available_boxes", box_label)
                    possible_by_oil = int(input_oil / oil_ratio)
                    possible_by_package = int(input_package / package_ratio)
                    possible_by_boxes = int(input_boxes)
                    estimated_output = min(possible_by_oil, possible_by_package, possible_by_boxes)
                    remaining_oil = max(input_oil - (estimated_output * oil_ratio), 0)
                    remaining_package = max(input_package - (estimated_output * package_ratio), 0)
                    remaining_boxes = max(input_boxes - estimated_output, 0)
                    capacity_options = {
                        "Oil": possible_by_oil,
                        package_label: possible_by_package,
                        "Boxes": possible_by_boxes,
                    }
                    minimum_capacity = min(capacity_options.values())
                    limiting_factor = ", ".join(
                        name for name, capacity in capacity_options.items() if capacity == minimum_capacity
                    )
                    if len(set(capacity_options.values())) == 1:
                        limiting_factor = "Balanced"

                    if action == "produce":
                        requested_output = int_form("production_quantity", "Production quantity", 1)
                        if requested_output > estimated_output:
                            raise ValueError("Production quantity cannot exceed calculated output.")
                        oil_used = requested_output * oil_ratio
                        package_used = requested_output * package_ratio
                        boxes_used = requested_output
                        production_remaining_oil = max(input_oil - oil_used, 0)
                        production_remaining_package = max(input_package - package_used, 0)
                        production_remaining_boxes = max(input_boxes - boxes_used, 0)
                        consume_category_stock(cursor, "cooking_oil", oil_used)
                        consume_category_stock(cursor, package_category, package_used)
                        consume_category_stock(cursor, box_category, requested_output)
                        product_name = f"Finished {selected_ratio['label']}"
                        product_id = add_or_increment_inventory_item(
                            cursor,
                            product_name,
                            "finished_goods",
                            requested_output,
                            "Boxes",
                            0,
                        )
                        cursor.execute(
                            """
                            INSERT INTO usage_calculations (
                                box_size_kg, units_per_box, oil_ratio, plastic_ratio,
                                available_oil, available_plastic, available_boxes,
                                boxes_can_produce, remaining_oil, remaining_plastic,
                                remaining_boxes, calculated_by, record_type
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'production')
                            """,
                            (
                                selected_ratio["box_size_kg"],
                                units_per_box,
                                oil_ratio,
                                package_ratio,
                                input_oil,
                                input_package,
                                input_boxes,
                                requested_output,
                                production_remaining_oil,
                                production_remaining_package,
                                production_remaining_boxes,
                                current_user_id(),
                            ),
                        )
                        connection.commit()
                        log_audit(
                            "produce",
                            "inventory_item",
                            product_id,
                            f"Produced {requested_output} {selected_ratio['label']} boxes.",
                        )
                        flash(f"Added {requested_output} {selected_ratio['label']} boxes to finished goods inventory.", "success")
                        return redirect(url_for("main.inventory", category="finished_goods"))

                    result = {
                        "estimated_output": f"{estimated_output:,}",
                        "estimated_output_raw": estimated_output,
                        "remaining_oil": remaining_oil,
                        "remaining_package": remaining_package,
                        "remaining_boxes": remaining_boxes,
                        "limiting_factor": limiting_factor,
                        "input_oil": input_oil,
                        "input_package": input_package,
                        "input_boxes": input_boxes,
                        "box_label": selected_ratio["label"],
                        "oil_ratio": oil_ratio,
                        "package_ratio": package_ratio,
                        "package_category": package_category,
                        "package_label": package_label,
                        "box_category": box_category,
                        "box_stock_label": box_label,
                        "units_per_box": units_per_box,
                    }
                cursor.execute(
                    """
                    SELECT
                        calculation_id,
                        box_size_kg,
                        units_per_box,
                        oil_ratio,
                        plastic_ratio,
                        boxes_can_produce,
                        remaining_oil,
                        remaining_plastic,
                        remaining_boxes,
                        calculated_at
                    FROM usage_calculations
                    WHERE record_type = 'production'
                    ORDER BY calculated_at DESC, calculation_id DESC
                    LIMIT 5
                    """
                )
                recent_calculations = cursor.fetchall()
        except ValueError as exc:
            flash(str(exc), "danger")
        except Error:
            flash("Error calculating usage.", "danger")
    
        return render_template(
            "usage.html",
            oil=oil,
            result=result,
            box_ratios=BOX_RATIOS,
            selected_box_size=selected_box_size,
            selected_ratio=selected_ratio,
            selected_package_stock=packaging_stocks[selected_ratio["package_category"]],
            selected_box_stock=packaging_stocks[selected_ratio["box_category"]],
            input_values=input_values,
            production_readiness=production_readiness,
            recent_calculations=recent_calculations,
            usage_options={
                size: {
                    "label": ratio["label"],
                    "box_size_kg": ratio["box_size_kg"],
                    "units_per_box": ratio["units_per_box"],
                    "package_label": ratio["package_label"],
                    "package_quantity": packaging_stocks[ratio["package_category"]]["quantity"],
                    "package_quantity_str": packaging_stocks[ratio["package_category"]]["quantity_str"],
                    "box_label": ratio["box_label"],
                    "box_quantity": packaging_stocks[ratio["box_category"]]["quantity"],
                    "box_quantity_str": packaging_stocks[ratio["box_category"]]["quantity_str"],
                }
                for size, ratio in BOX_RATIOS.items()
            },
        )
    
    
    @main.route("/usage/history")
    @login_required
    def usage_history():
        return redirect(url_for("main.usage"))
