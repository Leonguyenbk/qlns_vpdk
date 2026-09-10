"""Truy vấn nhân sự: tìm kiếm, lọc, sắp xếp, phân trang, lọc theo phạm vi đơn vị."""
from __future__ import annotations

from sqlalchemy import or_, select

from ..extensions import db
from ..models import Employee, EmployeeAssignment, OrganizationUnit, Position

_SORT_MAP = {
    "full_name": Employee.full_name,
    "recruitment_date": Employee.recruitment_date,
    "updated_at": Employee.updated_at,
    "created_at": Employee.created_at,
    "employee_code": Employee.employee_code,
}


def get_by_id(employee_id: int, *, include_deleted: bool = False) -> Employee | None:
    emp = db.session.get(Employee, employee_id)
    if emp is None:
        return None
    if emp.is_deleted and not include_deleted:
        return None
    return emp


def get_by_code(code: str) -> Employee | None:
    return db.session.query(Employee).filter(Employee.employee_code == code).first()


def _current_unit_subquery():
    """id đơn vị hiện tại của mỗi nhân sự = phân công chính đang hiệu lực."""
    return (
        select(EmployeeAssignment.employee_id, EmployeeAssignment.unit_id, EmployeeAssignment.position_id)
        .where(
            EmployeeAssignment.is_primary.is_(True),
            EmployeeAssignment.end_date.is_(None),
        )
        .subquery()
    )


def list_for_export(
    *,
    scope,
    keyword: str | None = None,
    unit_id: int | None = None,
    position_id: int | None = None,
    status: str | None = None,
    employment_type: str | None = None,
    include_deleted: bool = False,
) -> list[Employee]:
    """Toàn bộ nhân sự khớp bộ lọc (không phân trang), sắp theo cơ cấu tổ chức."""
    cur = _current_unit_subquery()
    query = db.session.query(Employee).outerjoin(cur, cur.c.employee_id == Employee.id)
    if not include_deleted:
        query = query.filter(Employee.is_deleted.is_(False))
    if not scope.is_global:
        query = query.filter(cur.c.unit_id.in_(scope.unit_ids) if scope.unit_ids else db.false())
    if keyword:
        like = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Employee.employee_code.ilike(like),
                Employee.full_name.ilike(like),
                Employee.phone.ilike(like),
            )
        )
    if unit_id:
        query = query.filter(cur.c.unit_id == unit_id)
    if position_id:
        query = query.filter(cur.c.position_id == position_id)
    if status:
        query = query.filter(Employee.status == status)
    if employment_type:
        query = query.filter(Employee.employment_type == employment_type)

    _BIG = 1_000_000_000
    query = (
        query.outerjoin(OrganizationUnit, OrganizationUnit.id == cur.c.unit_id)
        .outerjoin(Position, Position.id == cur.c.position_id)
        .order_by(
            db.func.coalesce(OrganizationUnit.sort_index, _BIG).asc(),
            db.func.coalesce(Position.level, _BIG).asc(),
            Employee.full_name.asc(),
            Employee.id.asc(),
        )
    )
    return query.all()


def search(
    *,
    scope,
    keyword: str | None = None,
    unit_id: int | None = None,
    position_id: int | None = None,
    status: str | None = None,
    employment_type: str | None = None,
    include_deleted: bool = False,
    sort: str = "hierarchy",
    order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Employee], int]:
    cur = _current_unit_subquery()
    query = (
        db.session.query(Employee)
        .outerjoin(cur, cur.c.employee_id == Employee.id)
    )

    if not include_deleted:
        query = query.filter(Employee.is_deleted.is_(False))

    # --- Lọc theo phạm vi đơn vị của tài khoản (bắt buộc) ---
    # Nhân sự chưa có phân công (cur.c.unit_id IS NULL) chỉ hiển thị cho phạm vi toàn hệ thống.
    if not scope.is_global:
        if not scope.unit_ids:
            query = query.filter(db.false())
        else:
            query = query.filter(cur.c.unit_id.in_(scope.unit_ids))

    if keyword:
        like = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Employee.employee_code.ilike(like),
                Employee.full_name.ilike(like),
                Employee.phone.ilike(like),
            )
        )
    if unit_id:
        query = query.filter(cur.c.unit_id == unit_id)
    if position_id:
        query = query.filter(cur.c.position_id == position_id)
    if status:
        query = query.filter(Employee.status == status)
    if employment_type:
        query = query.filter(Employee.employment_type == employment_type)

    total = query.order_by(None).count()

    if sort not in _SORT_MAP:
        # Mặc định: sắp theo cơ cấu tổ chức (đơn vị theo cây) rồi thứ hạng chức vụ.
        _BIG = 1_000_000_000
        query = (
            query.outerjoin(OrganizationUnit, OrganizationUnit.id == cur.c.unit_id)
            .outerjoin(Position, Position.id == cur.c.position_id)
            .order_by(
                db.func.coalesce(OrganizationUnit.sort_index, _BIG).asc(),
                db.func.coalesce(Position.level, _BIG).asc(),
                Employee.full_name.asc(),
                Employee.id.asc(),
            )
        )
    else:
        sort_col = _SORT_MAP[sort]
        sort_col = sort_col.desc() if order.lower() == "desc" else sort_col.asc()
        query = query.order_by(sort_col, Employee.id.desc())

    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return rows, total


def dashboard_counts(scope) -> dict:
    """Số liệu tổng quan cho Dashboard, tôn trọng phạm vi đơn vị."""
    cur = _current_unit_subquery()
    base = db.session.query(Employee).outerjoin(cur, cur.c.employee_id == Employee.id).filter(
        Employee.is_deleted.is_(False)
    )
    if not scope.is_global:
        if not scope.unit_ids:
            base = base.filter(db.false())
        else:
            base = base.filter(cur.c.unit_id.in_(scope.unit_ids))

    total_working = base.filter(Employee.status == "WORKING").count()

    by_status_rows = (
        base.with_entities(Employee.status, db.func.count(Employee.id))
        .group_by(Employee.status)
        .all()
    )
    by_unit_rows = (
        base.with_entities(cur.c.unit_id, db.func.count(Employee.id))
        .group_by(cur.c.unit_id)
        .all()
    )
    return {
        "total_working": total_working,
        "by_status": {k or "UNKNOWN": v for k, v in by_status_rows},
        "by_unit": {int(k): v for k, v in by_unit_rows if k is not None},
    }
