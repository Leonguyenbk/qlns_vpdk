"""Ngữ cảnh xác thực và các decorator kiểm tra quyền cho route."""
from __future__ import annotations

import functools
from typing import Callable

from flask import g, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models import User
from .exceptions import AuthenticationError, PermissionDeniedError


def load_current_user() -> User:
    """Xác thực JWT access token và nạp User tương ứng (cache trong g)."""
    if "current_user" in g:
        return g.current_user

    verify_jwt_in_request()
    claims = get_jwt()
    if claims.get("type") != "access":
        raise AuthenticationError("Token không phải access token.")

    identity = get_jwt_identity()
    user = db.session.get(User, int(identity)) if identity is not None else None
    if user is None:
        raise AuthenticationError("Tài khoản không tồn tại.")
    if not user.is_active:
        raise AuthenticationError("Tài khoản đã bị khóa hoặc ngừng hoạt động.")

    g.current_user = user
    return user


def current_user() -> User:
    return load_current_user()


def get_request_meta() -> dict:
    return {
        "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent"),
    }


def auth_required(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        load_current_user()
        return fn(*args, **kwargs)

    return wrapper


def require_permission(*required: str, require_all: bool = False) -> Callable:
    """Bắt buộc đăng nhập và có (tất cả / ít nhất một) permission trong danh sách.

    Backend luôn kiểm tra quyền ở đây, không phụ thuộc việc frontend ẩn nút.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            user = load_current_user()
            codes = user.permission_codes()
            ok = (
                all(c in codes for c in required)
                if require_all
                else any(c in codes for c in required)
            )
            if not ok:
                raise PermissionDeniedError(
                    f"Bạn thiếu quyền: {', '.join(required)}."
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
