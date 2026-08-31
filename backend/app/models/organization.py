"""Model cơ cấu đơn vị (dạng cây)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin


class OrganizationUnit(TimestampMixin, db.Model):
    __tablename__ = "organization_units"
    __table_args__ = (
        UniqueConstraint("code", name="uq_organization_units_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization_units.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    address: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent: Mapped["OrganizationUnit | None"] = relationship(
        "OrganizationUnit", remote_side="OrganizationUnit.id", backref="children"
    )

    def to_dict(self, include_relations: bool = False) -> dict:
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "unit_type": self.unit_type,
            "parent_id": self.parent_id,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if include_relations:
            data["parent"] = (
                {"id": self.parent.id, "code": self.parent.code, "name": self.parent.name}
                if self.parent
                else None
            )
        return data


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
