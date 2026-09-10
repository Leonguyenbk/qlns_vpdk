"""Model RBAC: vai trò, quyền, gán vai trò và phạm vi đơn vị."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    Table,
    Column,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


role_permissions = Table(
    "role_permissions",
    db.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_roles = Table(
    "user_roles",
    db.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(db.Model):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255))

    def to_dict(self) -> dict:
        return {"id": self.id, "code": self.code, "description": self.description}


class Role(TimestampMixin, db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Vai trò hệ thống không được xóa; SYSTEM_ADMIN được bảo vệ đặc biệt
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions: Mapped[list[Permission]] = relationship(
        Permission, secondary=role_permissions, lazy="selectin"
    )

    def permission_codes(self) -> set[str]:
        return {p.code for p in self.permissions}

    def to_dict(self, include_permissions: bool = True) -> dict:
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "is_system": self.is_system,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if include_permissions:
            data["permissions"] = sorted(self.permission_codes())
        return data


class UserUnitScope(TimestampMixin, db.Model):
    """Phạm vi đơn vị của tài khoản.

    - scope_type = GLOBAL  : toàn hệ thống (unit_id = NULL)
    - scope_type = UNIT    : đúng 1 đơn vị
    - scope_type = SUBTREE : 1 đơn vị và toàn bộ đơn vị con
    Một tài khoản có thể có nhiều bản ghi phạm vi.
    """

    __tablename__ = "user_unit_scopes"
    __table_args__ = (
        UniqueConstraint("user_id", "scope_type", "unit_id", name="uq_user_unit_scope"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scope_type: Mapped[str] = mapped_column(String(10), nullable=False)  # GLOBAL|UNIT|SUBTREE
    unit_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization_units.id", ondelete="CASCADE"), nullable=True
    )

    unit = relationship("OrganizationUnit")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scope_type": self.scope_type,
            "unit_id": self.unit_id,
            "unit": {"id": self.unit.id, "code": self.unit.code, "name": self.unit.name}
            if self.unit
            else None,
        }
