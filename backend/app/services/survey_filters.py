"""Tiện ích lọc dùng chung cho danh sách phản hồi và thống kê khảo sát."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from ..common.exceptions import ValidationError
from ..common.utils import parse_date, utcnow
from ..permissions import constants as perms

DATE_PRESETS = {"today", "7d", "30d", "this_month", "this_quarter", "this_year"}


def _start_of_day(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _end_of_day(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc)


def resolve_date_range(args) -> tuple[datetime | None, datetime | None]:
    """Trả về (từ, đến) theo `date_from`/`date_to` (YYYY-MM-DD) hoặc `preset`."""
    date_from = args.get("date_from")
    date_to = args.get("date_to")
    if date_from or date_to:
        start = _start_of_day(parse_date(date_from, "date_from")) if date_from else None
        end = _end_of_day(parse_date(date_to, "date_to")) if date_to else None
        return start, end

    preset = args.get("preset")
    if not preset:
        return None, None
    if preset not in DATE_PRESETS:
        raise ValidationError(
            f"Khoảng thời gian lọc không hợp lệ. Chọn một trong: {', '.join(sorted(DATE_PRESETS))}."
        )
    today = utcnow().date()
    if preset == "today":
        start = end = today
    elif preset == "7d":
        start, end = today - timedelta(days=6), today
    elif preset == "30d":
        start, end = today - timedelta(days=29), today
    elif preset == "this_month":
        start, end = today.replace(day=1), today
    elif preset == "this_quarter":
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        start, end = today.replace(month=q_start_month, day=1), today
    else:  # this_year
        start, end = today.replace(month=1, day=1), today
    return _start_of_day(start), _end_of_day(end)


def apply_response_filters(query, args, *, response_model):
    """Lọc theo khoảng thời gian, chi nhánh, dịch vụ, quầy, cán bộ (khi có trong query)."""
    start, end = resolve_date_range(args)
    if start:
        query = query.filter(response_model.submitted_at >= start)
    if end:
        query = query.filter(response_model.submitted_at <= end)
    for field, column in (
        ("branch_id", response_model.branch_id),
        ("service_id", response_model.service_id),
        ("counter_id", response_model.counter_id),
        ("employee_id", response_model.employee_id),
    ):
        value = args.get(field)
        if value not in (None, ""):
            try:
                query = query.filter(column == int(value))
            except (TypeError, ValueError):
                raise ValidationError(f"Giá trị lọc '{field}' không hợp lệ.")
    return query


def apply_branch_scope(query, *, actor, scope, column):
    """Giới hạn theo phạm vi đơn vị của tài khoản, trừ khi có quyền xem toàn bộ chi nhánh."""
    if scope.is_global or perms.SURVEY_MANAGE_ALL_BRANCHES in actor.permission_codes():
        return query
    return scope.filter_unit_column(query, column)
