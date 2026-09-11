"""Route xác thực (đăng nhập CHUNG cho cả platform).

Trả token trong body — mọi SPA (nhân sự + gọi số) đều dùng Bearer. Cookie JWT
vẫn được đặt kèm (dự phòng, vô hại) nhưng không còn gì phụ thuộc nó từ khi
các trang gọi số chuyển hết sang React.
"""
from __future__ import annotations

from flask import Blueprint, make_response, request
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from ...common.auth_context import current_user, get_request_meta
from ...common.exceptions import ValidationError
from ...common.responses import success
from ...services import auth_service
from ...schemas import change_password_schema, login_schema
from .._helpers import validated_json

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _with_cookies(result: dict, message: str):
    """Bọc phản hồi success() và gắn cookie JWT nếu có token trong result."""
    resp = make_response(*success(result, message))
    if result.get("access_token"):
        set_access_cookies(resp, result["access_token"])
    if result.get("refresh_token"):
        set_refresh_cookies(resp, result["refresh_token"])
    return resp


@bp.post("/login")
def login():
    data = validated_json(login_schema)
    result = auth_service.login(
        data.get("username", ""), data.get("password", ""), meta=get_request_meta()
    )
    return _with_cookies(result, "Đăng nhập thành công")


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    claims = get_jwt()
    result = auth_service.refresh(
        claims["jti"], get_jwt_identity(), meta=get_request_meta()
    )
    return _with_cookies(result, "Làm mới token thành công")


@bp.post("/logout")
@jwt_required(refresh=True)
def logout():
    claims = get_jwt()
    auth_service.logout(claims["jti"])
    resp = make_response(*success(None, "Đăng xuất thành công"))
    unset_jwt_cookies(resp)
    return resp


@bp.get("/me")
def me():
    user = current_user()
    return success(user.to_dict(include_permissions=True))


@bp.put("/change-password")
def change_password():
    user = current_user()
    data = validated_json(change_password_schema)
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if not old_password or not new_password:
        raise ValidationError("Vui lòng nhập mật khẩu hiện tại và mật khẩu mới.")
    auth_service.change_password(user, old_password, new_password, meta=get_request_meta())
    return success(None, "Đổi mật khẩu thành công. Vui lòng đăng nhập lại.")
