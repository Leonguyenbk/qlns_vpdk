"""Các lớp lỗi nghiệp vụ dùng chung. Thông báo bằng tiếng Việt."""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Lỗi nghiệp vụ có kiểm soát, được error handler chuyển thành phản hồi JSON."""

    status_code = 400
    default_message = "Yêu cầu không hợp lệ."

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        errors: Any = None,
        payload: dict | None = None,
    ) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        if status_code is not None:
            self.status_code = status_code
        self.errors = errors
        self.payload = payload or {}


class ValidationError(AppError):
    status_code = 422
    default_message = "Dữ liệu đầu vào không hợp lệ."


class AuthenticationError(AppError):
    status_code = 401
    default_message = "Chưa xác thực hoặc phiên đăng nhập không hợp lệ."


class PermissionDeniedError(AppError):
    status_code = 403
    default_message = "Bạn không có quyền thực hiện thao tác này."


class NotFoundError(AppError):
    status_code = 404
    default_message = "Không tìm thấy dữ liệu."


class ConflictError(AppError):
    status_code = 409
    default_message = "Dữ liệu bị xung đột."


class BusinessRuleError(AppError):
    status_code = 400
    default_message = "Thao tác vi phạm quy tắc nghiệp vụ."
