"""Thông báo trong ứng dụng (giao việc/KPI). Kênh ngoài (email...) không tự
bật — chỉ cấu hình rõ ràng mới gửi (mục 10 yêu cầu)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..common.utils import utcnow
from ..extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
        # Chống thông báo trùng lặp cho cùng người/loại/đối tượng/ngày
        UniqueConstraint("user_id", "type", "entity_type", "entity_id", "dedupe_day", name="uq_notification_dedupe"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    dedupe_day: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "title": self.title,
            "body": self.body,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
