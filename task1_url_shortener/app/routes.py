"""Application routes for UI and REST API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import or_

from app import db, limiter
from app.models import URL
from app.utils import (
    create_seed_data,
    generate_qr_code,
    generate_unique_short_code,
    hash_password,
    parse_expiry,
    validate_alias,
    validate_url,
    verify_password,
)

main_bp = Blueprint("main", __name__)


def _base_url() -> str:
    """Build canonical base URL for generated short links."""

    return request.host_url.rstrip("/")


def _json_error(message: str, status_code: int = 400):
    """Return a standardized JSON error response."""

    return jsonify({"success": False, "error": message}), status_code


def _find_by_code(code: str) -> URL | None:
    """Get link by generated code or custom alias."""

    return URL.query.filter(or_(URL.short_code == code, URL.custom_alias == code)).first()


def _wants_json_response() -> bool:
    """Determine whether the client prefers JSON over HTML."""

    return request.accept_mimetypes.best == "application/json" and (
        request.accept_mimetypes["application/json"]
        >= request.accept_mimetypes["text/html"]
    )


@main_bp.errorhandler(429)
def handle_rate_limit(err):
    """Handle rate limiting errors with a consistent JSON format."""

    return jsonify({"success": False, "error": "Rate limit exceeded. Try again soon."}), 429


@main_bp.route("/", methods=["GET"])
def index():
    """Render dashboard UI and create sample data on first run."""

    create_seed_data(_base_url())
    recent_links = URL.query.order_by(URL.created_at.desc()).limit(10).all()
    return render_template("index.html", links=recent_links)


@main_bp.route("/api/shorten", methods=["POST"])
@limiter.limit("10 per minute")
def shorten_url():
    """Create a shortened URL from a single long URL payload."""

    payload = request.get_json(silent=True) or {}
    original_url = payload.get("url")
    alias = payload.get("custom_alias")
    expires_at_input = payload.get("expires_at")
    password = payload.get("password")

    ok_url, normalized_or_error = validate_url(original_url)
    if not ok_url:
        return _json_error(normalized_or_error, 400)

    ok_alias, alias_or_error = validate_alias(alias)
    if not ok_alias:
        return _json_error(alias_or_error, 400)
    clean_alias = alias_or_error or None

    expiry = parse_expiry(expires_at_input)
    if expiry == "invalid":
        return _json_error("Invalid expiry format. Use ISO-8601 datetime.", 400)
    if expiry == "past":
        return _json_error("Expiry time must be in the future.", 400)

    if clean_alias:
        conflict = _find_by_code(clean_alias)
        if conflict:
            return _json_error("Custom alias is already in use.", 400)

    short_code = generate_unique_short_code(current_app.config["SHORT_CODE_LENGTH"])
    record = URL(
        original_url=normalized_or_error,
        short_code=short_code,
        custom_alias=clean_alias,
        expires_at=expiry,
        password_hash=hash_password(password),
        is_active=True,
    )

    final_code = record.public_code()
    short_url = f"{_base_url()}/{final_code}"
    record.qr_code_filename = generate_qr_code(short_url, final_code)

    db.session.add(record)
    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "message": "Short URL created successfully.",
                "data": {
                    **record.to_dict(_base_url()),
                    "qr_code_url": url_for(
                        "static",
                        filename=f"qrcodes/{record.qr_code_filename}",
                        _external=True,
                    ),
                },
            }
        ),
        201,
    )


@main_bp.route("/api/shorten/bulk", methods=["POST"])
@limiter.limit("10 per minute")
def bulk_shorten():
    """Create shortened URLs for a list of URLs in one request."""

    payload = request.get_json(silent=True) or {}
    items = payload.get("urls")
    if not isinstance(items, list) or not items:
        return _json_error("Request body must include a non-empty 'urls' array.", 400)

    results = []
    for item in items:
        url_value = item.get("url") if isinstance(item, dict) else item
        ok_url, normalized_or_error = validate_url(url_value)
        if not ok_url:
            results.append({"url": url_value, "success": False, "error": normalized_or_error})
            continue

        short_code = generate_unique_short_code(current_app.config["SHORT_CODE_LENGTH"])
        record = URL(original_url=normalized_or_error, short_code=short_code, is_active=True)
        short_url = f"{_base_url()}/{short_code}"
        record.qr_code_filename = generate_qr_code(short_url, short_code)
        db.session.add(record)
        db.session.flush()
        results.append(
            {
                "url": normalized_or_error,
                "success": True,
                "short_url": short_url,
                "short_code": short_code,
                "id": record.id,
            }
        )

    db.session.commit()
    return jsonify({"success": True, "data": results}), 201


@main_bp.route("/api/links", methods=["GET"])
def list_links():
    """Return recent links for dashboard analytics table."""

    limit = min(int(request.args.get("limit", 50)), 200)
    links = URL.query.order_by(URL.created_at.desc()).limit(limit).all()
    return jsonify({"success": True, "data": [link.to_dict(_base_url()) for link in links]}), 200


@main_bp.route("/preview/<string:short_code>", methods=["GET"])
def preview_link(short_code: str):
    """Show link metadata preview before redirect."""

    record = _find_by_code(short_code)
    if not record:
        return _json_error("Short URL not found.", 404)
    if not record.is_active or record.is_expired():
        return _json_error("This short URL is inactive or expired.", 404)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "short_code": short_code,
                    "original_url": record.original_url,
                    "created_at": record.created_at.isoformat(),
                    "expires_at": record.expires_at.isoformat() if record.expires_at else None,
                    "click_count": record.click_count,
                    "last_accessed_at": (
                        record.last_accessed_at.isoformat()
                        if record.last_accessed_at
                        else None
                    ),
                    "password_protected": bool(record.password_hash),
                },
            }
        ),
        200,
    )


@main_bp.route("/qrcodes/<path:filename>", methods=["GET"])
def serve_qrcode(filename: str):
    """Serve generated QR code image files."""

    return send_from_directory(current_app.config["QR_CODE_DIR"], filename)


@main_bp.route("/<string:short_code>", methods=["GET", "POST"])
def redirect_short_url(short_code: str):
    """Resolve short code and redirect to destination URL."""

    record = _find_by_code(short_code)
    if not record:
        return _json_error("Short URL not found.", 404)

    if not record.is_active:
        return _json_error("This short URL is inactive.", 404)

    if record.is_expired():
        return _json_error("This short URL has expired.", 404)

    if record.password_hash:
        provided = request.values.get("password", "")
        if not verify_password(record.password_hash, provided):
            if _wants_json_response():
                return _json_error("Password required or incorrect.", 400)
            return (
                render_template(
                    "protected.html",
                    short_code=short_code,
                    error="Password required or incorrect.",
                ),
                400,
            )

    record.click_count += 1
    record.last_accessed_at = datetime.now(timezone.utc)
    db.session.commit()

    return redirect(record.original_url, code=301)
