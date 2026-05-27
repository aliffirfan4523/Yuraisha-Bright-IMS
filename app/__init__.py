import os
from datetime import timedelta

from flask import Flask
from dotenv import load_dotenv


def create_app():
    """Create and configure the Flask application."""
    load_dotenv()

    app = Flask(__name__)
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key and os.getenv("FLASK_ENV") == "production":
        raise RuntimeError("SECRET_KEY must be set in production.")

    app.config["SECRET_KEY"] = secret_key or "dev-secret-key-change-me"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "localhost")
    app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", "3306"))
    app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
    app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "")
    app.config["MYSQL_DATABASE"] = os.getenv("MYSQL_DATABASE", "yuraisha_inventory")

    from app.routes import main

    app.register_blueprint(main)

    return app
