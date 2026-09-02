"""Model cơ cấu đơn vị (dạng cây)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
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
    # Thứ tự duyệt cây (DFS) — dùng để sắp xếp nhân sự theo cơ cấu tổ chức.
    sort_index: Mapped[int | None] = mapped_column(Integer, index=True)

    parent: Mapped["OrganizationUnit | None"] = relationship(
        "OrganizationUnit", remote_side="OrganizationUnit.id", backref="children"
    )

    @property
    def group_unit(self) -> "OrganizationUnit | None":
        """Đơn vị cấp Phòng / Chi nhánh gần nhất (chính nó nếu nó là phòng/chi nhánh)."""
        node: "OrganizationUnit | None" = self
        seen: set[int] = set()
        while node is not None and node.id not in seen:
            seen.add(node.id)
            if node.unit_type in ("DEPARTMENT", "BRANCH"):
                return node
            node = node.parent
        return None

    @property
    def group_name(self) -> str:
        """Tên cột "Phòng / Chi nhánh"."""
        g = self.group_unit
        return g.name if g is not None else self.name

    @property
    def section_name(self) -> str | None:
        """Tên cột "Bộ phận" — chỉ khi đơn vị là cấp bộ phận/tổ (SECTION)."""
        return self.name if self.unit_type == "SECTION" else None

    @property
    def display_path(self) -> str:
        """Chuỗi 1 dòng kèm ngữ cảnh cha: "CN Đồng Xuân | Bộ phận Kỹ thuật…".

        Bỏ cấp trụ sở/văn phòng tỉnh (HEAD_OFFICE); nối các cấp còn lại từ trên
        xuống bằng " | ". Đơn vị cấp phòng/chi nhánh chỉ hiện chính tên nó.
        """
        chain: list[str] = []
        node: "OrganizationUnit | None" = self
        seen: set[int] = set()
        while node is not None and node.id not in seen:
            seen.add(node.id)
            if node.unit_type != "HEAD_OFFICE":
                chain.append(node.name)
            node = node.parent
        return " | ".join(reversed(chain)) or self.name

    def to_dict(self, include_relations: bool = False) -> dict:
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "path": self.display_path,
            "group_name": self.group_name,
            "section_name": self.section_name,
            "unit_type": self.unit_type,
            "parent_id": self.parent_id,
            "sort_index": self.sort_index,
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
