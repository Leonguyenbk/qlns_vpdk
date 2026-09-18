"""Đăng ký toàn bộ blueprint của platform.

    app/modules/
    ├── auth/      -> đăng nhập CHUNG (JWT) cho mọi module
    ├── nhansu/    -> quản lý nhân sự, đơn vị, chức vụ, tài khoản, vai trò, nhật ký
    ├── goiso/     -> gọi số / kiosk (lớp tương thích, giữ nguyên đường dẫn cũ)
    ├── tasks/     -> Giao việc – Theo dõi nhiệm vụ
    ├── kpi/       -> Đánh giá KPI (danh mục sản phẩm, bộ tiêu chí, kỳ, chấm điểm)
    ├── surveys/   -> Khảo sát – Đánh giá mức độ hài lòng (quản trị + công khai)
    └── announcements/ -> Bảng tin nội bộ và phân quyền người nhận
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

    # --- Module Giao việc – Theo dõi nhiệm vụ – Đánh giá KPI ---
    from .tasks.routes import bp as tasks_bp
    from .kpi.routes import bp as kpi_bp

    app.register_blueprint(tasks_bp)
    app.register_blueprint(kpi_bp)

    # --- Module Khảo sát – Đánh giá mức độ hài lòng ---
    from .surveys.routes import bp as surveys_bp
    from .surveys.routes import options_bp as survey_options_bp
    from .surveys.routes import public_bp as public_surveys_bp
    from .surveys.routes import questions_bp as survey_questions_bp
    from .surveys.routes import sections_bp as survey_sections_bp

    for bp in (
        surveys_bp,
        survey_questions_bp,
        survey_options_bp,
        survey_sections_bp,
        public_surveys_bp,
    ):
        app.register_blueprint(bp)

    # --- Bảng tin / thông báo nội bộ ---
    from .announcements.routes import bp as announcements_bp

    app.register_blueprint(announcements_bp)
