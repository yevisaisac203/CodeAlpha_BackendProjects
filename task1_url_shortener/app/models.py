"""Database models for the URL shortener."""

from __future__ import annotations

from datetime import datetime, timezone

from app import db


class URL(db.Model):
    """Model that stores shortened URL records."""

    __tablename__ = "urls"

    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)
    short_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    custom_alias = db.Column(db.String(32), unique=True, nullable=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    click_count = db.Column(db.Integer, nullable=False, default=0)
    last_accessed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    password_hash = db.Column(db.String(255), nullable=True)
    qr_code_filename = db.Column(db.String(255), nullable=True)

    def is_expired(self) -> bool:
        """Check whether a link has passed its expiry timestamp."""

        return bool(self.expires_at and datetime.now(timezone.utc) > self.expires_at)

    def public_code(self) -> str:
        """Return user-facing code (alias or generated code)."""

        return self.custom_alias or self.short_code

    def to_dict(self, base_url: str | None = None) -> dict:
        """Serialize model to API response dictionary."""

        code = self.public_code()
        short_url = f"{base_url}/{code}" if base_url else code
        return {
            "id": self.id,
            "original_url": self.original_url,
            "short_code": self.short_code,
            "custom_alias": self.custom_alias,
            "short_url": short_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "click_count": self.click_count,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "has_password": bool(self.password_hash),
            "qr_code_filename": self.qr_code_filename,
        }
