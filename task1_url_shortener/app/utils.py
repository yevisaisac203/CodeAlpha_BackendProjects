"""Utility helpers for URL shortener business logic."""

from __future__ import annotations

import os
import secrets
import string
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urlparse

import qrcode
import validators
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import URL

ALPHANUMERIC = string.ascii_letters + string.digits


def normalize_url(url: str) -> str:
    """Normalize a URL and prepend scheme if omitted."""

    candidate = (url or "").strip()
    if not candidate:
        return ""
    parsed = urlparse(candidate)
    if not parsed.scheme:
        candidate = f"https://{candidate}"
    return candidate


def validate_url(url: str) -> tuple[bool, str]:
    """Validate URL and return (is_valid, normalized_url_or_error)."""

    normalized = normalize_url(url)
    if not normalized:
        return False, "URL is required."
    if not validators.url(normalized):
        return False, "Invalid URL format. Include a valid domain."
    return True, normalized


def validate_alias(alias: str | None) -> tuple[bool, str]:
    """Validate custom alias constraints."""

    if not alias:
        return True, ""
    clean = alias.strip()
    if len(clean) < 3 or len(clean) > 32:
        return False, "Custom alias must be 3-32 characters long."
    allowed = set(string.ascii_letters + string.digits + "-_")
    if not all(ch in allowed for ch in clean):
        return False, "Custom alias only allows letters, numbers, '-' and '_'."
    return True, clean


def parse_expiry(expires_at: str | None):
    """Parse ISO timestamp for expiry or return None."""

    if not expires_at:
        return None
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return "invalid"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if parsed <= datetime.now(timezone.utc):
        return "past"
    return parsed


def generate_unique_short_code(length: int = 6) -> str:
    """Generate a unique short code not currently used."""

    for _ in range(20):
        code = "".join(secrets.choice(ALPHANUMERIC) for _ in range(length))
        exists = URL.query.filter(
            (URL.short_code == code) | (URL.custom_alias == code)
        ).first()
        if not exists:
            return code
    raise RuntimeError("Could not generate unique short code after multiple attempts.")


def hash_password(password: str | None) -> str | None:
    """Hash a password if provided."""

    if not password:
        return None
    return generate_password_hash(password)


def verify_password(password_hash: str | None, plain_password: str | None) -> bool:
    """Validate provided password against hash."""

    if not password_hash:
        return True
    return bool(plain_password and check_password_hash(password_hash, plain_password))


def generate_qr_code(short_url: str, filename_hint: str) -> str:
    """Generate and save QR code image for a short URL."""

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(short_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    safe_hint = "".join(ch for ch in filename_hint if ch.isalnum() or ch in "-_")[:40]
    filename = f"{safe_hint or 'link'}_{secrets.token_hex(4)}.png"
    output_path = os.path.join(current_app.config["QR_CODE_DIR"], filename)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    with open(output_path, "wb") as file_obj:
        file_obj.write(buffer.getvalue())

    return filename


def create_seed_data(base_url: str) -> None:
    """Create sample data on first run for a richer dashboard."""

    if URL.query.count() > 0:
        return

    samples = [
        ("https://flask.palletsprojects.com/", "flaskdocs"),
        ("https://www.sqlalchemy.org/", "alchemy"),
        ("https://realpython.com/", None),
    ]

    for original, alias in samples:
        code = generate_unique_short_code(length=current_app.config["SHORT_CODE_LENGTH"])
        record = URL(
            original_url=original,
            short_code=code,
            custom_alias=alias,
            is_active=True,
        )
        final_code = alias or code
        record.qr_code_filename = generate_qr_code(f"{base_url}/{final_code}", final_code)
        db.session.add(record)

    db.session.commit()
