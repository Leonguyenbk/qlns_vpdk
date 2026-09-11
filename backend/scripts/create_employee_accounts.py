"""Tạo tài khoản đăng nhập cho nhân sự đang làm việc chưa có tài khoản, để mỗi
người có thể đăng nhập dùng "Công việc của tôi"/"KPI của tôi".

    python -m scripts.create_employee_accounts            # dry-run, in báo cáo
    python -m scripts.create_employee_accounts --commit   # ghi vào CSDL

Vai trò/phạm vi được suy ra từ CHỨC VỤ + ĐƠN VỊ hiện có (dữ liệu đã có sẵn
trong hệ thống, không tự bịa thêm), bám theo đúng bảng thẩm quyền mục 17.1
tài liệu KPI dự thảo (docs/TASK_KPI_ANALYSIS.md):

  - Giám đốc/Phó Giám đốc VPĐKĐĐ (chức vụ cấp 10/20, thuộc "Ban Giám đốc" cấp
    Phòng/Ban của TOÀN Văn phòng — không phải Ban Giám đốc của một Chi nhánh)
      -> OFFICE_LEADER, phạm vi GLOBAL.
  - Giám đốc/Phó Giám đốc Chi nhánh, Trưởng phòng/Phó Trưởng phòng (cấp
    10/20/30/35 tại một Chi nhánh hoặc một Phòng của Văn phòng)
      -> UNIT_HEAD, phạm vi SUBTREE(Phòng/Chi nhánh đó).
  - Trưởng bộ phận/Phó trưởng bộ phận/Tổ trưởng/Tổ phó (cấp 40/45/50/55 —
    quản lý một Bộ phận/Tổ NHỎ HƠN bên trong Chi nhánh; bảng thẩm quyền tài
    liệu KHÔNG nêu cấp này có thẩm quyền theo dõi/đánh giá chính thức)
      -> TASK_ASSIGNER, phạm vi SUBTREE(đúng đơn vị được phân công).
  - Còn lại (Chuyên viên/Nhân viên/Văn thư/Thủ quỹ...)
      -> STAFF, chỉ tự phục vụ (Công việc của tôi/KPI của tôi).

Mật khẩu khởi tạo: CHUNG cho toàn bộ tài khoản mới (theo yêu cầu — hệ thống
hiện CHƯA có cơ chế bắt đổi mật khẩu lần đầu). Mọi người tự đổi tại màn hình
"Đổi mật khẩu" sau khi đăng nhập lần đầu.

Chỉ xử lý nhân sự: chưa liên kết tài khoản nào (employee_id), đang WORKING,
chưa xoá mềm. Nhân sự thuộc đơn vị CHƯA có username_prefix (xem migration
0009) được liệt kê riêng để xử lý sau — KHÔNG bỏ qua âm thầm.
"""
from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from sqlalchemy import text

DEFAULT_PASSWORD = "Vpdk@2026"

_OFFICE_LEADER_LEVELS = {10, 20}
_UNIT_HEAD_LEVELS = {10, 20, 30, 35}
_TASK_ASSIGNER_LEVELS = {40, 45, 50, 55}


def run(commit: bool) -> None:
    load_dotenv()
    from app import create_app
    from app.extensions import db
    from app.models import Employee, EmployeeAssignment, OrganizationUnit, Position, Role, User, UserUnitScope
    from app.permissions.constants import ROLE_OFFICE_LEADER, ROLE_STAFF, ROLE_TASK_ASSIGNER, ROLE_UNIT_HEAD
    from app.services.username_service import generate_username

    app = create_app(os.getenv("FLASK_ENV"))
    with app.app_context():
        needed_roles = {ROLE_OFFICE_LEADER, ROLE_UNIT_HEAD, ROLE_TASK_ASSIGNER, ROLE_STAFF}
        roles_by_code = {r.code: r for r in db.session.query(Role).filter(Role.code.in_(needed_roles))}
        missing = needed_roles - set(roles_by_code)
        if missing:
            raise SystemExit(f"Thiếu vai trò {missing} — chạy 'flask --app wsgi db upgrade' trước.")

        head_office_root = db.session.query(OrganizationUnit.id).filter(
            OrganizationUnit.unit_type == "HEAD_OFFICE"
        ).scalar()

        rows = (
            db.session.query(Employee, EmployeeAssignment, Position)
            .join(EmployeeAssignment, EmployeeAssignment.employee_id == Employee.id)
            .join(Position, Position.id == EmployeeAssignment.position_id)
            .filter(
                Employee.is_deleted.is_(False),
                Employee.status == "WORKING",
                EmployeeAssignment.end_date.is_(None),
                EmployeeAssignment.is_primary.is_(True),
            )
            .all()
        )
        already_linked = {r[0] for r in db.session.execute(text(
            "SELECT employee_id FROM users WHERE employee_id IS NOT NULL"
        ))}

        created, no_prefix, role_counts = [], [], {}
        used_usernames_this_run: set[str] = set()

        for emp, assignment, position in rows:
            if emp.id in already_linked:
                continue
            unit = db.session.get(OrganizationUnit, assignment.unit_id)
            if unit is None:
                continue
            group = unit.group_unit or unit
            if not group.username_prefix:
                no_prefix.append(
                    f"  {emp.employee_code} '{emp.full_name}' — đơn vị '{unit.name}' "
                    f"(Phòng/Chi nhánh '{group.name}') chưa có username_prefix"
                )
                continue

            username = generate_username(emp.full_name, unit)
            base_user, n = username, 2
            while username in used_usernames_this_run:
                username = f"{base_user}{n}"
                n += 1
            used_usernames_this_run.add(username)

            level = position.level
            if level in _OFFICE_LEADER_LEVELS and group.unit_type == "DEPARTMENT" and group.parent_id == head_office_root:
                role_code, scope = ROLE_OFFICE_LEADER, ("GLOBAL", None)
            elif level in _UNIT_HEAD_LEVELS:
                role_code, scope = ROLE_UNIT_HEAD, ("SUBTREE", group.id)
            elif level in _TASK_ASSIGNER_LEVELS:
                role_code, scope = ROLE_TASK_ASSIGNER, ("SUBTREE", unit.id)
            else:
                role_code, scope = ROLE_STAFF, None

            role_counts[role_code] = role_counts.get(role_code, 0) + 1
            # Lưu CHUỖI (không lưu đối tượng ORM) — tránh DetachedInstanceError
            # khi in báo cáo sau khi đã ra khỏi app context / session commit.
            created.append((emp.employee_code, emp.full_name, username, role_code, scope, unit.name, position.name))

            if commit:
                user = User(username=username, full_name=emp.full_name, employee_id=emp.id, is_active=True)
                user.set_password(DEFAULT_PASSWORD)
                user.roles.append(roles_by_code[role_code])
                if scope:
                    user.unit_scopes.append(UserUnitScope(scope_type=scope[0], unit_id=scope[1]))
                db.session.add(user)

        if commit:
            db.session.commit()

    print(f"{'ĐÃ TẠO' if commit else 'SẼ TẠO khi --commit'}: {len(created)} tài khoản")
    for role_code, count in sorted(role_counts.items()):
        print(f"  {role_code}: {count}")
    print()
    for emp_code, full_name, username, role_code, scope, unit_name, pos_name in created[:25]:
        print(f"  {emp_code:8s} {full_name:28s} {pos_name:20s} {unit_name:32s} -> {username:22s} [{role_code}]")
    if len(created) > 25:
        print(f"  ... và {len(created) - 25} tài khoản khác")

    if no_prefix:
        print(f"\nCHƯA TẠO ĐƯỢC — đơn vị chưa có username_prefix ({len(no_prefix)}):")
        print("\n".join(no_prefix[:30]))
        if len(no_prefix) > 30:
            print(f"  ... và {len(no_prefix) - 30} dòng khác")

    print(f"\nMật khẩu khởi tạo cho toàn bộ tài khoản mới: {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    run(ap.parse_args().commit)
