from flask import Blueprint

from app.route_support import inject_global_values, protect_post_requests
from app.route_modules import admin, alerts, auth, inventory, public, reports, tracking, transactions, usage


main = Blueprint("main", __name__)
main.before_app_request(protect_post_requests)
main.app_context_processor(inject_global_values)

for module in (public, auth, admin, inventory, usage, alerts, tracking, transactions, reports):
    module.register_routes(main)
