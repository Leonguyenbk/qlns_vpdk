"""Tạo tài khoản quản trị hệ thống đầu tiên.

Chạy:
    python -m scripts.create_admin
hoặc:
    flask --app wsgi create-admin

Thông tin lấy từ biến môi trường ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL / ADMIN_FULL_NAME.
Script idempotent: nếu tài khoản đã tồn tại thì mặc định chỉ đảm bảo vai trò/phạm vi.
Đặt ADMIN_RESET_PASSWORD=true để cập nhật mật khẩu của tài khoản đã tồn tại.
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv


def run_create_admin() -> None:
    load_dotenv()
    from app import create_app
    from app.extensions import db
    from app.models import Role, User, UserUnitScope
    from app.permissions.constants import ROLE_SYSTEM_ADMIN
    from app.services.auth_service import revoke_all_for_user

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    full_name = os.getenv("ADMIN_FULL_NAME", "Quản trị hệ thống")
    reset_password = os.getenv("ADMIN_RESET_PASSWORD", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    if not password or len(password) < 8:
        print("LỖI: ADMIN_PASSWORD phải có ít nhất 8 ký tự (đặt trong .env).")
        sys.exit(1)

    app = create_app(os.getenv("FLASK_ENV"))
    with app.app_context():
        role = db.session.query(Role).filter(Role.code == ROLE_SYSTEM_ADMIN).first()
        if role is None:
            print("LỖI: Chưa seed vai trò. Hãy chạy 'flask --app wsgi db upgrade' trước.")
            sys.exit(1)

        user = db.session.query(User).filter(User.username == username).first()
        created = False
        if user is None:
            user = User(username=username, full_name=full_name, email=email, is_active=True)
            user.set_password(password)
            db.session.add(user)
            created = True
        elif reset_password:
            user.set_password(password)
            user.failed_login_count = 0
            user.locked_until = None
            revoke_all_for_user(user.id)

        if role not in user.roles:
            user.roles.append(role)

        has_global = any(s.scope_type == "GLOBAL" for s in user.unit_scopes)
        if not has_global:
            user.unit_scopes.append(UserUnitScope(scope_type="GLOBAL", unit_id=None))

        db.session.commit()
        action = "Đã tạo" if created else "Đã cập nhật"
        print(f"{action} tài khoản quản trị: {username}")
        print(f"  - Vai trò: {ROLE_SYSTEM_ADMIN}")
        print("  - Phạm vi: GLOBAL (toàn hệ thống)")
        if not created:
            if reset_password:
                print("  - Mật khẩu: đã đặt lại từ ADMIN_PASSWORD")
            else:
                print("  - Mật khẩu: giữ nguyên (đặt ADMIN_RESET_PASSWORD=true để đặt lại)")


if __name__ == "__main__":
    run_create_admin()
