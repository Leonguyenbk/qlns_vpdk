"""Cấu hình ứng dụng đọc từ biến môi trường."""
from __future__ import annotations

import os
from datetime import timedelta


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "900"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "1209600"))
    )
    JWT_ERROR_MESSAGE_KEY = "message"

    # Token đọc từ HEADER (SPA nhân sự dùng Bearer) HOẶC COOKIE (trang Jinja goiso
    # đăng nhập một lần cho cả platform — SSO cùng origin).
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SAMESITE = "Lax"
    # TODO(P8): bật JWT_COOKIE_CSRF_PROTECT + gửi header CSRF từ JS goiso.
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_SESSION_COOKIE = False
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_REFRESH_COOKIE_PATH = "/"
    JWT_COOKIE_SECURE = os.getenv("FLASK_ENV", "development").lower() == "production"
    _cookie_domain = os.getenv("COOKIE_DOMAIN", "").strip()
    if _cookie_domain:
        JWT_COOKIE_DOMAIN = _cookie_domain

    # CORS
    CORS_ORIGINS = _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173"))

    # Chính sách đăng nhập
    LOGIN_MAX_FAILED_ATTEMPTS = int(os.getenv("LOGIN_MAX_FAILED_ATTEMPTS", "5"))
    LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PROPAGATE_EXCEPTIONS = True
    # Không trả stack trace cho client
    DEBUG = False
    TESTING = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True  # trả thông tin lỗi chi tiết trong test
    # Test chạy trên SQLite in-memory để không phụ thuộc MySQL
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_ENGINE_OPTIONS = {}
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    LOGIN_MAX_FAILED_ATTEMPTS = 3
    LOGIN_LOCKOUT_MINUTES = 15


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(name: str | None = None):
    env = (name or os.getenv("FLASK_ENV", "development")).lower()
    return _CONFIG_MAP.get(env, DevelopmentConfig)
