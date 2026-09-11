"""Sinh/đổi tên đăng nhập (username) theo đơn vị — dùng khi tạo tài khoản
hàng loạt và khi nhân sự chuyển đơn vị (đổi tiền tố tự động, theo yêu cầu).

QUY TẮC (giữ đúng cách đặt username đã dùng cho tài khoản gọi số di trú, để
tài khoản mới/đổi tên hoà chung một kiểu, không lẫn hai kiểu khác nhau):
    <tiền_tố_đơn_vị>.<tên_gọi><chữ_cái_đầu_các_từ_còn_lại_theo_thứ_tự>
Ví dụ: "Mai Đức Giáp" ở đơn vị tiền tố "bmt" -> "bmt.giapmd"
       (tên gọi "Giáp" là từ cuối cùng; "m","đ" là chữ đầu của "Mai","Đức").

Username KHÔNG phải khoá ngoại ở bất kỳ bảng nào khác (mọi chức năng dùng
users.id/employee_id) — đổi username an toàn cho dữ liệu, chỉ ảnh hưởng đăng
nhập, nên người bị đổi PHẢI được thông báo lại tên đăng nhập mới.
"""
from __future__ import annotations

import re
import unicodedata

from ..extensions import db
from ..models import EmployeeAssignment, OrganizationUnit, User
from .audit_service import record_audit


def _strip_diacritics(s: str) -> str:
    s = (s or "").replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _ascii_token(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _strip_diacritics(s).lower())


def name_slug(full_name: str) -> str:
    """"Mai Đức Giáp" -> "giapmd" (tên gọi = từ cuối; phần đầu = chữ cái đầu
    các từ còn lại, theo đúng thứ tự xuất hiện trong họ tên)."""
    tokens = [t for t in (full_name or "").strip().split() if t]
    if not tokens:
        return ""
    given = _ascii_token(tokens[-1])
    initials = "".join(_ascii_token(t)[:1] for t in tokens[:-1])
    return f"{given}{initials}"


def unit_username_prefix(unit: OrganizationUnit | None) -> str | None:
    """Tiền tố username của một đơn vị — lấy từ đơn vị cấp Phòng/Chi nhánh
    gần nhất (``group_unit``), KHÔNG lấy theo Tổ/Bộ phận nhỏ hơn bên trong."""
    if unit is None:
        return None
    group = unit.group_unit or unit
    return group.username_prefix


def _is_taken(username: str, *, exclude_user_id: int | None) -> bool:
    q = db.session.query(User.id).filter(User.username == username)
    if exclude_user_id is not None:
        q = q.filter(User.id != exclude_user_id)
    return db.session.query(q.exists()).scalar()


def generate_username(full_name: str, unit: OrganizationUnit | None, *, exclude_user_id: int | None = None) -> str | None:
    """Sinh username duy nhất từ họ tên + đơn vị. Trả về None nếu đơn vị chưa
    có tiền tố cấu hình (``organization_units.username_prefix``)."""
    prefix = unit_username_prefix(unit)
    if not prefix:
        return None
    base = name_slug(full_name)
    if not base:
        return None
    candidate = f"{prefix}.{base}"
    n = 2
    while _is_taken(candidate, exclude_user_id=exclude_user_id):
        candidate = f"{prefix}.{base}{n}"
        n += 1
    return candidate


def sync_username_for_employee(employee, *, actor_id: int | None, meta: dict | None = None) -> dict | None:
    """Sau khi nhân sự chuyển đơn vị: nếu đã có tài khoản đăng nhập liên kết,
    tính lại username theo đơn vị MỚI; đổi nếu khác tiền tố hiện tại.

    Trả về ``{"old_username", "new_username"}`` nếu có đổi, ``None`` nếu
    không có tài khoản liên kết hoặc tiền tố không đổi (không đổi username
    một cách vô cớ khi ở lại cùng Phòng/Chi nhánh, chỉ đổi bộ phận/tổ)."""
    user = db.session.query(User).filter(User.employee_id == employee.id).first()
    if user is None:
        return None
    # Truy vấn thẳng CSDL (không dùng employee.assignments đã nạp sẵn trong
    # session) — sau assign_primary()/end_assignment(), collection quan hệ
    # trong bộ nhớ có thể chưa phản ánh bản ghi phân công MỚI vừa flush().
    current = (
        db.session.query(EmployeeAssignment)
        .filter(
            EmployeeAssignment.employee_id == employee.id,
            EmployeeAssignment.is_primary.is_(True),
            EmployeeAssignment.end_date.is_(None),
        )
        .first()
    )
    if current is None or current.unit is None:
        return None
    # Dùng employee.full_name (nguồn dữ liệu gốc) chứ không phải user.full_name,
    # để không sinh sai nếu hai trường này từng lệch nhau.
    new_username = generate_username(employee.full_name, current.unit, exclude_user_id=user.id)
    if not new_username or new_username == user.username:
        return None

    old_username = user.username
    user.username = new_username
    record_audit(
        user_id=actor_id, action="user.username_renamed", entity_type="user", entity_id=user.id,
        old_values={"username": old_username}, new_values={"username": new_username},
        **(meta or {}),
    )
    return {"old_username": old_username, "new_username": new_username}
