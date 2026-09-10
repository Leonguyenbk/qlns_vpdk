"""Truy vấn dữ liệu đơn vị."""
from __future__ import annotations

from ..extensions import db
from ..models import Employee, EmployeeAssignment, OrganizationUnit, UnitPositionLimit


def get_by_id(unit_id: int) -> OrganizationUnit | None:
    return db.session.get(OrganizationUnit, unit_id)


def get_by_code(code: str) -> OrganizationUnit | None:
    return (
        db.session.query(OrganizationUnit)
        .filter(OrganizationUnit.code == code)
        .first()
    )


def list_all(*, only_active: bool | None = None) -> list[OrganizationUnit]:
    q = db.session.query(OrganizationUnit)
    if only_active is True:
        q = q.filter(OrganizationUnit.is_active.is_(True))
    return q.order_by(OrganizationUnit.code).all()


def build_tree(units: list[OrganizationUnit]) -> list[dict]:
    """Dựng cây từ danh sách phẳng (một lượt duyệt)."""
    nodes: dict[int, dict] = {}
    for u in units:
        nodes[u.id] = {**u.to_dict(), "children": []}
    roots: list[dict] = []
    for u in units:
        node = nodes[u.id]
        if u.parent_id and u.parent_id in nodes:
            nodes[u.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


def descendant_ids(root_id: int) -> set[int]:
    result: set[int] = {root_id}
    frontier = {root_id}
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


def has_dependent_data(unit_id: int) -> bool:
    """Đơn vị có nhân sự đang phân công hoặc có dữ liệu lịch sử / giới hạn chức vụ."""
    has_assignment = (
        db.session.query(EmployeeAssignment.id)
        .filter(EmployeeAssignment.unit_id == unit_id)
        .first()
        is not None
    )
    if has_assignment:
        return True
    has_limit = (
        db.session.query(UnitPositionLimit.id)
        .filter(UnitPositionLimit.unit_id == unit_id)
        .first()
        is not None
    )
    if has_limit:
        return True
    has_child = (
        db.session.query(OrganizationUnit.id)
        .filter(OrganizationUnit.parent_id == unit_id)
        .first()
        is not None
    )
    return has_child
