"""Di trú dữ liệu Gọi số: SQLite (hethong_v2.db) -> bảng goiso_* trong CSDL chung.

    python -m scripts.migrate_goiso --source "D:/.../hethong_v2.db"            # dry-run
    python -m scripts.migrate_goiso --source "D:/.../hethong_v2.db" --commit   # ghi

- Giữ nguyên khoá chính (branch id, queue id...) để các tham chiếu không đứt.
- Idempotent: chạy lại chỉ cập nhật, không nhân bản (ON DUPLICATE KEY UPDATE).
- Ghi log theo từng bảng: đọc (nguồn) / ghi (đích) / bỏ qua / lỗi.
"""
from __future__ import annotations

import argparse
import os
import sqlite3

from dotenv import load_dotenv
from sqlalchemy import text

# (bảng nguồn SQLite, bảng đích MySQL, cột khoá chính)
_TABLES = [
    ("branches", "goiso_branches", ["id"]),
    ("config", "goiso_config", ["branch_id", "key"]),
    ("counters_status", "goiso_counters_status", ["branch_id", "counter_id"]),
    ("visitor_stats", "goiso_visitor_stats", ["branch_id", "date_record"]),
    ("queue", "goiso_queue", ["id"]),
    ("appointments", "goiso_appointments", ["id"]),
    ("devices", "goiso_devices", ["device_id"]),
]


def _q(name: str) -> str:
    return f"`{name}`"


def run(source: str, commit: bool) -> None:
    if not os.path.exists(source):
        raise SystemExit(f"Không thấy file nguồn: {source}")
    load_dotenv()

    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row

    from app import create_app
    from app.extensions import db

    app = create_app(os.getenv("FLASK_ENV"))
    report: list[str] = []
    grand = {"read": 0, "written": 0, "skipped": 0, "errors": 0}

    with app.app_context():
        # cột đích thực tế của từng bảng goiso_*
        insp = db.inspect(db.engine)
        dest_cols = {t[1]: {c["name"] for c in insp.get_columns(t[1])} for t in _TABLES}

        conn = db.engine.connect()
        trans = conn.begin()
        try:
            for s_tbl, d_tbl, pk in _TABLES:
                try:
                    rows = src.execute(f"SELECT * FROM {s_tbl}").fetchall()
                except sqlite3.OperationalError:
                    report.append(f"{d_tbl:24s} nguồn không có bảng {s_tbl} — bỏ qua")
                    continue
                cols = [c for c in (rows[0].keys() if rows else []) if c in dest_cols[d_tbl]]
                if not rows:
                    report.append(f"{d_tbl:24s} đọc 0")
                    continue
                non_pk = [c for c in cols if c not in pk]
                col_list = ", ".join(_q(c) for c in cols)
                val_list = ", ".join(f":{c}" for c in cols)
                upd = ", ".join(f"{_q(c)}=VALUES({_q(c)})" for c in non_pk) or f"{_q(pk[0])}={_q(pk[0])}"
                sql = text(
                    f"INSERT INTO {d_tbl} ({col_list}) VALUES ({val_list}) "
                    f"ON DUPLICATE KEY UPDATE {upd}"
                )
                w = e = 0
                for r in rows:
                    grand["read"] += 1
                    try:
                        conn.execute(sql, {c: r[c] for c in cols})
                        w += 1
                    except Exception as exc:  # noqa: BLE001
                        e += 1
                        if e <= 3:
                            report.append(f"  [lỗi] {d_tbl} {dict(r).get(pk[0])}: {exc}")
                grand["written"] += w
                grand["errors"] += e
                report.append(f"{d_tbl:24s} đọc {len(rows):5d}  ghi {w:5d}  lỗi {e}")

            if commit:
                trans.commit()
            else:
                trans.rollback()
        except Exception:
            trans.rollback()
            raise
        finally:
            conn.close()

    print("\n".join(report))
    print(
        f"\nTỔNG  đọc {grand['read']}  ghi {grand['written']}  lỗi {grand['errors']}  "
        f"({'ĐÃ GHI' if commit else 'dry-run — thêm --commit'})"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.getenv("GOISO_DB", ""), help="Đường dẫn hethong_v2.db")
    ap.add_argument("--commit", action="store_true")
    a = ap.parse_args()
    run(a.source, a.commit)
