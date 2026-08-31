"""Tiện ích dùng chung cho các route."""
from __future__ import annotations

from flask import request

from ..common.auth_context import current_user, get_request_meta
from ..common.exceptions import ValidationError
from ..permissions.scope import resolve_user_scope


def json_body() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        if request.method in ("POST", "PUT", "PATCH") and request.data:
            raise ValidationError("Body phải là JSON hợp lệ.")
        return {}
    if not isinstance(data, dict):
        raise ValidationError("Body phải là một đối tượng JSON.")
    return data


def validated_json(schema) -> dict:
    """Đọc JSON và kiểm tra kiểu dữ liệu bằng Marshmallow schema."""
    return schema.load(json_body())


def actor_and_scope():
    user = current_user()
    return user, resolve_user_scope(user)


def audit_meta() -> dict:
    return get_request_meta()
