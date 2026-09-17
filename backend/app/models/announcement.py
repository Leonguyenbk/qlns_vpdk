"""Bảng tin nội bộ và phạm vi người nhận thông báo."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..common.utils import utcnow
from ..extensions import db
from .base import TimestampMixin


ANNOUNCEMENT_STATUSES = {"draft", "published", "archived"}
ANNOUNCEMENT_AUDIENCES = {"ALL", "UNIT", "ROLE", "USER"}


announcement_units = Table(
    "announcement_units",
    db.metadata,
    Column("announcement_id", Integer, ForeignKey("announcements.id", ondelete="CASCADE"), primary_key=True),
    Column("unit_id", Integer, ForeignKey("organization_units.id", ondelete="CASCADE"), primary_key=True),
)

announcement_roles = Table(
    "announcement_roles",
    db.metadata,
    Column("announcement_id", Integer, ForeignKey("announcements.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

announcement_users = Table(
    "announcement_users",
    db.metadata,
    Column("announcement_id", Integer, ForeignKey("announcements.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class Announcement(TimestampMixin, db.Model):
    __tablename__ = "announcements"
    __table_args__ = (
        Index("ix_announcements_status_published", "status", "published_at"),
        Index("ix_announcements_pinned", "is_pinned", "published_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="Thông báo")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    audience_type: Mapped[str] = mapped_column(String(10), nullable=False, default="ALL")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    units = relationship("OrganizationUnit", secondary=announcement_units, lazy="selectin")
    roles = relationship("Role", secondary=announcement_roles, lazy="selectin")
    users = relationship("User", secondary=announcement_users, lazy="selectin")

    def to_dict(self, *, is_read: bool = False) -> dict:
        target_items: list[dict] = []
        if self.audience_type == "UNIT":
            target_items = [{"id": u.id, "name": u.name} for u in self.units]
        elif self.audience_type == "ROLE":
            target_items = [{"id": r.id, "name": r.name} for r in self.roles]
        elif self.audience_type == "USER":
            target_items = [{"id": u.id, "name": u.full_name} for u in self.users]

        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "status": self.status,
            "audience_type": self.audience_type,
            "audience_items": target_items,
            "is_pinned": self.is_pinned,
            "published_at": _iso(self.published_at),
            "expires_at": _iso(self.expires_at),
            "created_by": self.created_by,
            "creator_name": self.creator.full_name if self.creator else None,
            "is_read": is_read,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }


class AnnouncementRead(db.Model):
    __tablename__ = "announcement_reads"
    __table_args__ = (
        UniqueConstraint("announcement_id", "user_id", name="uq_announcement_read"),
        Index("ix_announcement_reads_user", "user_id", "read_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    announcement_id: Mapped[int] = mapped_column(
        ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
