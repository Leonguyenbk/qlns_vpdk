"""Gán vai trò STAFF (tự phục vụ tối thiểu) cho các tài khoản đang KHÔNG có
vai trò nào — ví dụ tạo qua "Thêm tài khoản" mà quên tích vai trò. Một tài
khoản không có vai trò nào thì kể cả nhiệm vụ/KPI của chính mình cũng không
xem được (task.view_own/kpi.view_own đều thiếu), dù họ có thể đang là người
tham gia/được giao việc thật trong hệ thống.

    python -m scripts.backfill_staff_role            # dry-run, in danh sách
    python -m scripts.backfill_staff_role --commit   # ghi user_roles

Chỉ thêm vai trò STAFF cho tài khoản đang có 0 vai trò — không đụng tài
khoản đã có ít nhất 1 vai trò (kể cả vai trò không liên quan Giao việc/KPI,
ví dụ GOISO_COUNTER thuần) và không xoá/sửa gì khác.
"""
from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from sqlalchemy import text


def run(commit: bool) -> None:
    load_dotenv()
    from app import create_app
    from app.extensions import db
    from app.permissions.constants import ROLE_STAFF

    app = create_app(os.getenv("FLASK_ENV"))
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()

        role_row = conn.execute(
            text("SELECT id FROM roles WHERE code=:c"), {"c": ROLE_STAFF}
        ).fetchone()
        if role_row is None:
            print(f"Chưa có vai trò {ROLE_STAFF} trong CSDL — chạy migration trước.")
            trans.rollback()
            conn.close()
            return
        staff_role_id = role_row.id

        no_role_users = conn.execute(
            text(
                "SELECT u.id, u.username, u.full_name FROM users u "
                "LEFT JOIN user_roles ur ON ur.user_id = u.id "
                "WHERE ur.user_id IS NULL"
            )
        ).fetchall()

        for u in no_role_users:
            if commit:
                conn.execute(
                    text("INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid)"),
                    {"uid": u.id, "rid": staff_role_id},
                )

        if commit:
            trans.commit()
        else:
            trans.rollback()
        conn.close()

    print(f"Tài khoản không có vai trò nào ({'ĐÃ GÁN STAFF' if commit else 'sẽ gán STAFF khi --commit'}): {len(no_role_users)}")
    for u in no_role_users:
        print(f"  [{u.username}] {u.full_name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    run(ap.parse_args().commit)
