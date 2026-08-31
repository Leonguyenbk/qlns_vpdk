"""Model chức vụ và giới hạn chức vụ theo đơn vị."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class Position(TimestampMixin, db.Model):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("code", name="uq_positions_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_managerial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "level": self.level,
            "description": self.description,
            "is_managerial": self.is_managerial,
            "is_active": self.is_active,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }


class UnitPositionLimit(TimestampMixin, db.Model):
    __tablename__ = "unit_position_limits"
    __table_args__ = (
        UniqueConstraint("unit_id", "position_id", name="uq_unit_position_limit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("organization_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # NULL = không giới hạn
    max_holders: Mapped[int | None] = mapped_column(Integer, nullable=True)

    unit = relationship("OrganizationUnit")
    position = relationship("Position")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "position_id": self.position_id,
            "max_holders": self.max_holders,
            "position": self.position.to_dict() if self.position else None,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
