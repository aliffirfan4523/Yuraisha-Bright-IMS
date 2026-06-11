from datetime import date, datetime, timedelta
from flask import flash, redirect, render_template, request, url_for
from mysql.connector import Error

from app.route_support import *

BOX_RATIOS = {
    "1": {
        "label": "17kg Box",
        "box_size_kg": 1.0,
        "units_per_box": 17,
        "package_label": "1kg Plastic Packs",
        "box_label": "17kg Empty Boxes",
    },
}

def register_routes(main):
    @main.route("/usage", methods=["GET", "POST"])
    @login_required
    def usage():
        oil = {"quantity": 0, "quantity_str": "0"}
        package = {"quantity": 0, "quantity_str": "0"}
        box = {"quantity": 0, "quantity_str": "0"}
        
        result = None
        production_readiness = []
        
        selected_box_size = request.form.get("box_size", "1")
        selected_ratio = BOX_RATIOS.get(selected_box_size, BOX_RATIOS["1"])
        
        input_values = {
            "oil": 0,
            "package": 0,
            "boxes": 0,
        }
    
        try:
            with db_cursor() as (connection, cursor):
                cursor.execute("SELECT material_name, current_quantity FROM tbl_material")
                materials = cursor.fetchall()
                for mat in materials:
                    if mat["material_name"] == "Cooking Oil":
                        oil["quantity"] = float(mat["current_quantity"])
                        oil["quantity_str"] = f"{oil['quantity']:,.0f}"
                    elif mat["material_name"] == "1kg Plastic Packs":
                        package["quantity"] = float(mat["current_quantity"])
                        package["quantity_str"] = f"{package['quantity']:,.0f}"
                    elif mat["material_name"] == "17kg Empty Boxes":
                        box["quantity"] = float(mat["current_quantity"])
                        box["quantity_str"] = f"{box['quantity']:,.0f}"
                        
                # Determine capacity
                ratio = selected_ratio
                oil_needed = ratio["box_size_kg"] * ratio["units_per_box"]
                possible_by_oil = int(oil["quantity"] / oil_needed) if oil_needed else 0
                possible_by_package = int(package["quantity"] / ratio["units_per_box"]) if ratio["units_per_box"] else 0
                possible_by_boxes = int(box["quantity"])
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
                        "size": "1",
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
                
                if request.method == "GET":
                    input_values["oil"] = oil["quantity"]
                    input_values["package"] = package["quantity"]
                    input_values["boxes"] = box["quantity"]
                else:
                    input_values["oil"] = request.form.get("available_oil", oil["quantity"])
                    input_values["package"] = request.form.get("available_package", package["quantity"])
                    input_values["boxes"] = request.form.get("available_boxes", box["quantity"])
                    
                if request.method == "POST":
                    action = request.form.get("action", "calculate")
                    input_oil = float(input_values["oil"])
                    input_package = float(input_values["package"])
                    input_boxes = float(input_values["boxes"])
                    
                    units_per_box = selected_ratio["units_per_box"]
                    oil_ratio = selected_ratio["box_size_kg"] * units_per_box
                    package_ratio = units_per_box
                    
                    possible_by_oil = int(input_oil / oil_ratio)
                    possible_by_package = int(input_package / package_ratio)
                    possible_by_boxes = int(input_boxes)
                    
                    estimated_output = min(possible_by_oil, possible_by_package, possible_by_boxes)
                    remaining_oil = max(input_oil - (estimated_output * oil_ratio), 0)
                    remaining_package = max(input_package - (estimated_output * package_ratio), 0)
                    remaining_boxes = max(input_boxes - estimated_output, 0)
                    
                    capacity_options = {
                        "Oil": possible_by_oil,
                        ratio["package_label"]: possible_by_package,
                        "Boxes": possible_by_boxes,
                    }
                    minimum_capacity = min(capacity_options.values())
                    limiting_factor = ", ".join(
                        name for name, cap in capacity_options.items() if cap == minimum_capacity
                    )
                    if len(set(capacity_options.values())) == 1:
                        limiting_factor = "Balanced"

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
                        "package_label": ratio["package_label"],
                        "box_stock_label": ratio["box_label"],
                        "units_per_box": units_per_box,
                    }
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
            selected_package_stock=package,
            selected_box_stock=box,
            input_values=input_values,
            production_readiness=production_readiness,
            recent_calculations=[],
            usage_options={
                size: {
                    "label": r["label"],
                    "box_size_kg": r["box_size_kg"],
                    "units_per_box": r["units_per_box"],
                    "package_label": r["package_label"],
                    "package_quantity": package["quantity"],
                    "package_quantity_str": package["quantity_str"],
                    "box_label": r["box_label"],
                    "box_quantity": box["quantity"],
                    "box_quantity_str": box["quantity_str"],
                }
                for size, r in BOX_RATIOS.items()
            },
        )
    
    @main.route("/usage/history")
    @login_required
    def usage_history():
        return redirect(url_for("main.usage"))
