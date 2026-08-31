"""Application Factory."""
from __future__ import annotations

import logging

from flask import Flask, jsonify
from sqlalchemy import text

from .config import get_config
from .errors import register_error_handlers
from .extensions import cors, db, jwt, migrate
from .logging_config import configure_logging


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    config = get_config(config_name)
    app.config.from_object(config)

    if (
        not app.config.get("SECRET_KEY")
        or not app.config.get("JWT_SECRET_KEY")
        or not app.config.get("SQLALCHEMY_DATABASE_URI")
    ):
        raise RuntimeError(
            "Thiếu SECRET_KEY, JWT_SECRET_KEY hoặc DATABASE_URL. "
            "Hãy cấu hình bằng biến môi trường."
        )

    configure_logging(app.config.get("LOG_LEVEL", "INFO"))

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # Import model để Alembic/relationship nhận diện
    from . import models  # noqa: F401

    _register_jwt_callbacks(app)
    register_error_handlers(app)

    @app.before_request
    def _reset_request_scoped_cache():
        # Bảo đảm ngữ cảnh xác thực được nạp lại cho từng request
        from flask import g

        g.pop("current_user", None)

    from .modules import register_blueprints

    register_blueprints(app)

    _register_health(app)
    _register_cli(app)

    logging.getLogger("app").info("Ứng dụng khởi tạo với cấu hình: %s", config.__name__)
    return app


def _register_jwt_callbacks(app: Flask) -> None:
    from .models import RefreshToken

    @jwt.token_in_blocklist_loader
    def _check_revoked(_jwt_header, jwt_payload) -> bool:
        # Chỉ theo dõi refresh token bằng jti
        if jwt_payload.get("type") != "refresh":
            return False
        jti = jwt_payload["jti"]
        row = db.session.query(RefreshToken.revoked).filter(RefreshToken.jti == jti).first()
        return bool(row and row[0])

    def _unauth_response(message: str, status: int = 401):
        return (
            jsonify({"success": False, "message": message, "data": None, "errors": None}),
            status,
        )

    @jwt.unauthorized_loader
    def _missing_token(reason):  # noqa: ANN001
        return _unauth_response("Thiếu hoặc sai định dạng token xác thực.")

    @jwt.invalid_token_loader
    def _invalid_token(reason):  # noqa: ANN001
        return _unauth_response("Token không hợp lệ.")

    @jwt.expired_token_loader
    def _expired_token(_h, _p):
        return _unauth_response("Token đã hết hạn.")

    @jwt.revoked_token_loader
    def _revoked_token(_h, _p):
        return _unauth_response("Token đã bị thu hồi.")


def _register_health(app: Flask) -> None:
    @app.get("/api/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            db_ok = True
        except Exception:  # pragma: no cover
            db_ok = False
        status = 200 if db_ok else 503
        return (
            jsonify(
                {
                    "success": db_ok,
                    "message": "OK" if db_ok else "Không kết nối được cơ sở dữ liệu",
                    "data": {"database": "up" if db_ok else "down"},
                    "errors": None,
                }
            ),
            status,
        )


def _register_cli(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command():
        """Seed dữ liệu mẫu (đơn vị, chức vụ, nhân sự)."""
        from scripts.seed import run_seed

        run_seed()

    @app.cli.command("create-admin")
    def create_admin_command():
        """Tạo tài khoản quản trị đầu tiên từ biến môi trường."""
        from scripts.create_admin import run_create_admin

        run_create_admin()
