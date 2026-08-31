"""Đăng ký toàn bộ blueprint theo module."""
from __future__ import annotations

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from .audit.routes import bp as audit_bp
    from .auth.routes import bp as auth_bp
    from .employees.routes import bp as employees_bp
    from .positions.routes import bp as positions_bp
    from .roles.routes import bp as roles_bp
    from .units.routes import bp as units_bp
    from .users.routes import bp as users_bp

    for bp in (auth_bp, employees_bp, units_bp, positions_bp, users_bp, roles_bp, audit_bp):
        app.register_blueprint(bp)
