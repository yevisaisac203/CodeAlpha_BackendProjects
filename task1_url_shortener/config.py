"""Application configuration module."""

from __future__ import annotations

import os
from datetime import timedelta


class Config:
    """Base configuration shared across environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///snapurl.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = "200 per day"
    SHORT_CODE_LENGTH = int(os.getenv("SHORT_CODE_LENGTH", "6"))
    DEFAULT_LINK_EXPIRY_DAYS = int(os.getenv("DEFAULT_LINK_EXPIRY_DAYS", "0"))
    QR_CODE_DIR = os.path.join("app", "static", "qrcodes")
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)


class DevelopmentConfig(Config):
    """Development settings."""

    DEBUG = True


class ProductionConfig(Config):
    """Production settings."""

    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
