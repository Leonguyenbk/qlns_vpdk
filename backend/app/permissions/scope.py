"""Giải quyết phạm vi đơn vị (unit scope) của tài khoản.

Mọi truy vấn danh sách/chi tiết nhân sự đều phải đi qua đây để lọc theo
phạm vi đơn vị mà tài khoản được phân công.
"""
from __future__ import annotations

from ..extensions import db
from ..models import OrganizationUnit, UserUnitScope


def _descendant_ids(root_ids: set[int]) -> set[int]:
    """Duyệt cây đơn vị (BFS) để lấy toàn bộ id đơn vị con của các gốc cho trước."""
    result: set[int] = set(root_ids)
    frontier = set(root_ids)
    while frontier:
        rows = (
            db.session.query(OrganizationUnit.id)
            .filter(OrganizationUnit.parent_id.in_(frontier))
            .all()
        )
        children = {r[0] for r in rows}
        new = children - result
        if not new:
            break
        result |= new
        frontier = new
    return result


class UnitScopeResolver:
    """Kết quả phân giải phạm vi cho một user.

    - is_global = True  -> thấy toàn bộ, không lọc.
    - unit_ids          -> tập id đơn vị được phép (đã bao gồm cây con nếu SUBTREE).
    """

    def __init__(self, is_global: bool, unit_ids: set[int]):
        self.is_global = is_global
        self.unit_ids = unit_ids

    def allows_unit(self, unit_id: int | None) -> bool:
        if self.is_global:
            return True
        if unit_id is None:
            return False
        return unit_id in self.unit_ids

    def filter_unit_column(self, query, column):
        """Áp điều kiện lọc theo cột unit_id vào query SQLAlchemy."""
        if self.is_global:
            return query
        if not self.unit_ids:
            # Không có phạm vi nào -> không thấy gì
            return query.filter(db.false())
        return query.filter(column.in_(self.unit_ids))


def resolve_user_scope(user) -> UnitScopeResolver:
    scopes: list[UserUnitScope] = list(user.unit_scopes)
    if any(s.scope_type == "GLOBAL" for s in scopes):
        return UnitScopeResolver(is_global=True, unit_ids=set())

    direct_ids = {s.unit_id for s in scopes if s.scope_type == "UNIT" and s.unit_id}
    subtree_roots = {s.unit_id for s in scopes if s.scope_type == "SUBTREE" and s.unit_id}

    unit_ids = set(direct_ids)
    if subtree_roots:
        unit_ids |= _descendant_ids(subtree_roots)
    return UnitScopeResolver(is_global=False, unit_ids=unit_ids)
