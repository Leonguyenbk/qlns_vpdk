"""Xử lý lỗi tập trung: chuyển mọi lỗi thành phản hồi JSON thống nhất."""
from __future__ import annotations

import logging

from flask import Flask
from marshmallow import ValidationError as MarshmallowValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from .common.exceptions import AppError
from .common.responses import error

logger = logging.getLogger("app.errors")


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _handle_app_error(exc: AppError):
        payload_data = exc.payload or None
        if exc.status_code >= 500:
            logger.exception("Lỗi ứng dụng: %s", exc.message)
        else:
            logger.info("Lỗi nghiệp vụ (%s): %s", exc.status_code, exc.message)
        return error(
            message=exc.message,
            status_code=exc.status_code,
            errors=exc.errors,
            data=payload_data,
        )

    @app.errorhandler(MarshmallowValidationError)
    def _handle_marshmallow(exc: MarshmallowValidationError):
        return error(
            message="Dữ liệu đầu vào không hợp lệ.",
            status_code=422,
            errors=exc.messages,
        )

    @app.errorhandler(IntegrityError)
    def _handle_integrity(exc: IntegrityError):
        logger.warning("Vi phạm ràng buộc CSDL: %s", exc)
        return error(
            message="Dữ liệu vi phạm ràng buộc toàn vẹn (trùng lặp hoặc tham chiếu không hợp lệ).",
            status_code=409,
        )

    @app.errorhandler(HTTPException)
    def _handle_http(exc: HTTPException):
        return error(
            message=exc.description or exc.name,
            status_code=exc.code or 500,
        )

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        # Không trả stack trace cho client ở production
        logger.exception("Loi khong mong doi: %s", repr(exc))
        if app.debug:
            import traceback

            return error(
                message=f"{type(exc).__name__}: {exc}",
                status_code=500,
                errors=traceback.format_exc().splitlines()[-12:],
            )
        return error(
            message="Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.", status_code=500
        )
