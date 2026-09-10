"""Đăng ký toàn bộ blueprint của platform.

    app/modules/
    ├── auth/      -> đăng nhập CHUNG (JWT) cho mọi module
    ├── nhansu/    -> quản lý nhân sự, đơn vị, chức vụ, tài khoản, vai trò, nhật ký
    └── goiso/     -> gọi số / kiosk (lớp tương thích, giữ nguyên đường dẫn cũ)
"""
from __future__ import annotations

from flask import Flask


def register_blueprints(app: Flask) -> None:
    # --- Auth chung ---
    from .auth.routes import bp as auth_bp

    app.register_blueprint(auth_bp)

    # --- Module Nhân sự ---
    from .nhansu.audit.routes import bp as audit_bp
    from .nhansu.employees.routes import bp as employees_bp
    from .nhansu.positions.routes import bp as positions_bp
    from .nhansu.roles.routes import bp as roles_bp
    from .nhansu.units.routes import bp as units_bp
    from .nhansu.users.routes import bp as users_bp

    for bp in (employees_bp, units_bp, positions_bp, users_bp, roles_bp, audit_bp):
        app.register_blueprint(bp)

    # --- Module Goiso (blueprint tương thích, giữ nguyên đường dẫn cũ) ---
    from .goiso.legacy_app import bp as goiso_compat_bp

    app.register_blueprint(goiso_compat_bp)
