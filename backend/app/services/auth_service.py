"""Nghiệp vụ xác thực: đăng nhập, làm mới token, đăng xuất, đổi mật khẩu."""
from __future__ import annotations

from datetime import timedelta

from flask import current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
)

from ..common.exceptions import AuthenticationError, ConflictError, ValidationError
from ..common.utils import ensure_aware, utcnow
from ..extensions import db
from ..models import RefreshToken, User
from .audit_service import record_audit


def _issue_tokens(user: User, *, meta: dict | None = None) -> dict:
    """Phát access + refresh token, lưu jti refresh để có thể thu hồi."""
    additional_claims = {"type": "access"}
    access_token = create_access_token(
        identity=str(user.id), additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    decoded = decode_token(refresh_token)
    rt = RefreshToken(
        jti=decoded["jti"],
        user_id=user.id,
        issued_at=utcnow(),
        expires_at=utcnow()
        + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
        user_agent=(meta or {}).get("user_agent", "")[:255] or None if meta else None,
        ip_address=(meta or {}).get("ip_address") if meta else None,
    )
    db.session.add(rt)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": int(
            current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()
        ),
    }


def login(username: str, password: str, *, meta: dict | None = None) -> dict:
    username = (username or "").strip()
    if not username or not password:
        raise ValidationError("Vui lòng nhập tên đăng nhập và mật khẩu.")

    user = db.session.query(User).filter(User.username == username).first()
    # Thông báo mơ hồ để tránh dò tài khoản
    generic_err = AuthenticationError("Tên đăng nhập hoặc mật khẩu không đúng.")

    if user is None:
        raise generic_err

    now = utcnow()
    if user.locked_until and ensure_aware(user.locked_until) > now:
        raise AuthenticationError(
            "Tài khoản đang tạm khóa do đăng nhập sai nhiều lần. Vui lòng thử lại sau."
        )
    if not user.is_active:
        raise AuthenticationError("Tài khoản đã bị khóa hoặc ngừng hoạt động.")

    if not user.check_password(password):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        max_attempts = current_app.config["LOGIN_MAX_FAILED_ATTEMPTS"]
        if user.failed_login_count >= max_attempts:
            user.locked_until = now + timedelta(
                minutes=current_app.config["LOGIN_LOCKOUT_MINUTES"]
            )
            user.failed_login_count = 0
        db.session.commit()
        raise generic_err

    # Đăng nhập thành công -> reset bộ đếm
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now

    tokens = _issue_tokens(user, meta=meta)
    record_audit(
        user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        ip_address=(meta or {}).get("ip_address"),
        user_agent=(meta or {}).get("user_agent"),
    )
    db.session.commit()
    return {"user": user.to_dict(include_permissions=True), **tokens}


def refresh(jti: str, user_id: int, *, meta: dict | None = None) -> dict:
    rt = db.session.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if rt is None or rt.revoked:
        raise AuthenticationError("Refresh token không hợp lệ hoặc đã bị thu hồi.")
    if ensure_aware(rt.expires_at) <= utcnow():
        raise AuthenticationError("Refresh token đã hết hạn.")

    user = db.session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise AuthenticationError("Tài khoản không hợp lệ.")

    # Xoay vòng refresh token: thu hồi cái cũ, phát cái mới
    rt.revoked = True
    rt.revoked_at = utcnow()
    tokens = _issue_tokens(user, meta=meta)
    db.session.commit()
    return tokens


def logout(jti: str) -> None:
    rt = db.session.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if rt and not rt.revoked:
        rt.revoked = True
        rt.revoked_at = utcnow()
    db.session.commit()


def revoke_all_for_user(user_id: int) -> int:
    rows = (
        db.session.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .all()
    )
    for r in rows:
        r.revoked = True
        r.revoked_at = utcnow()
    return len(rows)


def change_password(user: User, old_password: str, new_password: str, *, meta: dict | None = None) -> None:
    if not user.check_password(old_password):
        raise AuthenticationError("Mật khẩu hiện tại không đúng.")
    if len(new_password or "") < 8:
        raise ValidationError("Mật khẩu mới phải có ít nhất 8 ký tự.")
    if old_password == new_password:
        raise ConflictError("Mật khẩu mới không được trùng mật khẩu cũ.")

    user.set_password(new_password)
    # Đổi mật khẩu -> thu hồi toàn bộ refresh token đang hoạt động
    revoke_all_for_user(user.id)
    record_audit(
        user_id=user.id,
        action="auth.change_password",
        entity_type="user",
        entity_id=user.id,
        ip_address=(meta or {}).get("ip_address"),
        user_agent=(meta or {}).get("user_agent"),
    )
    db.session.commit()
