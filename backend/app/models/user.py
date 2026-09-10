"""Model tài khoản người dùng."""
from __future__ import annotations

from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin
from .rbac import Role, user_roles

_ph = PasswordHasher()


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Chống brute-force
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list[Role]] = relationship(
        Role, secondary=user_roles, lazy="selectin"
    )
    unit_scopes = relationship(
        "UserUnitScope", lazy="selectin", cascade="all, delete-orphan"
    )
    employee = relationship("Employee")

    # --- Mật khẩu ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = _ph.hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        try:
            _ph.verify(self.password_hash, raw_password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
        # Nâng cấp hash nếu tham số thay đổi
        if _ph.check_needs_rehash(self.password_hash):
            self.password_hash = _ph.hash(raw_password)
        return True

    # --- Quyền ---
    def permission_codes(self) -> set[str]:
        codes: set[str] = set()
        for role in self.roles:
            codes |= role.permission_codes()
        return codes

    def has_permission(self, code: str) -> bool:
        return code in self.permission_codes()

    def role_codes(self) -> set[str]:
        return {r.code for r in self.roles}

    def to_dict(self, include_permissions: bool = False) -> dict:
        data = {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "employee_id": self.employee_id,
            "is_active": self.is_active,
            "last_login_at": _iso(self.last_login_at),
            "roles": [r.to_dict(include_permissions=False) for r in self.roles],
            "unit_scopes": [s.to_dict() for s in self.unit_scopes],
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if include_permissions:
            data["permissions"] = sorted(self.permission_codes())
        return data
