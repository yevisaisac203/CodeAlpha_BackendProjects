"""Flask application factory and extensions initialization."""

from __future__ import annotations

import os

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config_map

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure a Flask application instance."""

    app = Flask(__name__, instance_relative_config=False)
    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_map.get(env_name, config_map["development"]))
    app.config["QR_CODE_DIR"] = os.path.join(app.root_path, "static", "qrcodes")

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    from app.routes import main_bp

    app.register_blueprint(main_bp)

    with app.app_context():
        from app.models import URL  # noqa: F401

        os.makedirs(app.config["QR_CODE_DIR"], exist_ok=True)
        db.create_all()

    return app
