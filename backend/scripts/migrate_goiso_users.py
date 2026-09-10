"""Di trú tài khoản từ hệ Gọi số (SQLite) sang bảng users chung của platform.

    python -m scripts.migrate_goiso_users            # dry-run, chỉ in báo cáo
    python -m scripts.migrate_goiso_users --commit   # ghi vào CSDL

Quy tắc:
- admin goiso  -> hợp nhất vào tài khoản 'admin' của platform (thêm vai trò GOISO_ADMIN).
                  KHÔNG đụng mật khẩu admin hiện có.
- nhân viên     -> tạo/cập nhật user cùng username, gán vai trò GOISO_COUNTER,
                  đặt goiso_branch_code = mã chi nhánh, giữ hash sha256 cũ ở
                  legacy_password_sha256 (đăng nhập lần đầu sẽ tự nâng cấp Argon2).
- Idempotent. Không xoá gì ở SQLite.
"""
from __future__ import annotations

import argparse
import os
import secrets
import sqlite3

from dotenv import load_dotenv


def _connect_goiso():
    load_dotenv()
    path = os.getenv("GOISO_DB")
    if not path or not os.path.exists(path):
        raise SystemExit(f"Không thấy GOISO_DB: {path!r}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def run(commit: bool) -> None:
    src = _connect_goiso()
    rows = src.execute(
        """SELECT u.id, u.username, u.full_name, u.password_hash, u.role,
                  u.active, b.code AS branch_code
             FROM users u LEFT JOIN branches b ON b.id = u.branch_id"""
    ).fetchall()

    from app import create_app
    from app.extensions import db
    from app.models import Role, User, UserUnitScope
    from app.permissions.constants import (
        ROLE_GOISO_ADMIN,
        ROLE_GOISO_COUNTER,
    )

    app = create_app(os.getenv("FLASK_ENV"))
    stats = {"source": len(rows), "created": 0, "updated": 0, "skipped": 0, "errors": 0}
    notes: list[str] = []

    with app.app_context():
        role_admin = db.session.query(Role).filter_by(code=ROLE_GOISO_ADMIN).first()
        role_counter = db.session.query(Role).filter_by(code=ROLE_GOISO_COUNTER).first()
        if not (role_admin and role_counter):
            raise SystemExit("Chưa seed vai trò GOISO_*. Chạy 'flask --app wsgi db upgrade' trước.")

        for r in rows:
            try:
                uname = (r["username"] or "").strip().lower()
                if not uname:
                    stats["skipped"] += 1
                    continue
                existing = db.session.query(User).filter_by(username=uname).first()

                if r["role"] == "admin":
                    target = existing or db.session.query(User).filter_by(username="admin").first()
                    if target is None:
                        notes.append(f"[skip] admin goiso '{uname}': chưa có tài khoản admin platform")
                        stats["skipped"] += 1
                        continue
                    have = {ro.code for ro in target.roles}
                    if ROLE_GOISO_ADMIN not in have:
                        # Chỉ THÊM, giữ nguyên các vai trò sẵn có (vd SYSTEM_ADMIN).
                        target.roles.append(role_admin)
                        notes.append(f"[admin] '{target.username}' += GOISO_ADMIN (giữ {sorted(have)})")
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                    continue

                # --- nhân viên trực quầy ---
                if existing is None:
                    u = User(
                        username=uname,
                        full_name=r["full_name"] or uname,
                        email=None,
                        is_active=bool(r["active"]),
                        goiso_branch_code=r["branch_code"],
                        legacy_password_sha256=r["password_hash"],
                    )
                    u.set_password(secrets.token_urlsafe(24))  # hash Argon2 vô dụng -> buộc dùng sha256 cũ
                    u.roles.append(role_counter)
                    db.session.add(u)
                    notes.append(
                        f"[create] {uname} -> GOISO_COUNTER @ chi nhánh {r['branch_code']}"
                    )
                    stats["created"] += 1
                else:
                    changed = False
                    if existing.goiso_branch_code != r["branch_code"]:
                        existing.goiso_branch_code = r["branch_code"]
                        changed = True
                    if role_counter not in existing.roles:
                        existing.roles.append(role_counter)
                        changed = True
                    if changed:
                        notes.append(f"[update] {uname} -> GOISO_COUNTER @ {r['branch_code']}")
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
            except Exception as exc:  # noqa: BLE001
                stats["errors"] += 1
                notes.append(f"[error] {r['username']}: {exc}")

        if commit:
            db.session.commit()
        else:
            db.session.rollback()

    print("\n".join(notes) or "(không có thay đổi)")
    print(
        f"\nnguồn={stats['source']}  tạo={stats['created']}  cập nhật={stats['updated']}  "
        f"bỏ qua={stats['skipped']}  lỗi={stats['errors']}  "
        f"({'ĐÃ GHI' if commit else 'dry-run — thêm --commit để ghi'})"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="Ghi vào CSDL (mặc định dry-run).")
    run(ap.parse_args().commit)
