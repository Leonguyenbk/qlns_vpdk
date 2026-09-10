"""Đánh lại chỉ số duyệt cây (`OrganizationUnit.sort_index`).

Dùng để sắp xếp danh sách nhân sự theo cơ cấu tổ chức: Văn phòng tỉnh
(Ban Giám đốc -> các phòng) rồi tới từng chi nhánh (Ban Giám đốc -> các bộ phận).

Gọi sau mỗi lần import "Phụ lục 4" và sau mỗi lần tạo/sửa/xoá đơn vị.
Thủ công: `flask --app wsgi reindex-units`.
"""
from __future__ import annotations

from ..extensions import db
from ..models import OrganizationUnit

# Thứ tự các anh em cùng cấp: phòng trước, rồi bộ phận, rồi chi nhánh.
_TYPE_RANK = {"HEAD_OFFICE": 0, "DEPARTMENT": 1, "SECTION": 2, "BRANCH": 3}


def _sibling_key(u: OrganizationUnit) -> tuple:
    name = (u.name or "").strip().lower()
    is_bgd = 0 if name.startswith("ban giám đốc") else 1  # Ban Giám đốc luôn đứng đầu
    # rồi theo loại (phòng trước chi nhánh), cuối cùng theo id = thứ tự trong file gốc
    return (is_bgd, _TYPE_RANK.get(u.unit_type, 9), u.id or 0)


def reindex_units() -> int:
    """Gán lại `sort_index` = 0,1,2,… theo thứ tự duyệt DFS. Trả về số đơn vị đã đánh."""
    units = db.session.query(OrganizationUnit).all()
    children: dict[int | None, list[OrganizationUnit]] = {}
    for u in units:
        children.setdefault(u.parent_id, []).append(u)
    for lst in children.values():
        lst.sort(key=_sibling_key)

    counter = 0

    def walk(node: OrganizationUnit) -> None:
        nonlocal counter
        node.sort_index = counter
        counter += 1
        for ch in children.get(node.id, []):
            walk(ch)

    for root in children.get(None, []):
        walk(root)

    # Đơn vị mồ côi (parent_id trỏ tới đơn vị không tồn tại) -> xếp sau cùng
    for u in units:
        if u.sort_index is None:
            u.sort_index = counter
            counter += 1

    db.session.flush()
    return counter
