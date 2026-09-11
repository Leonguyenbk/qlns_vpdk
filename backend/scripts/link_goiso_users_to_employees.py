"""Liên kết tài khoản Gọi số (đã có `goiso_branch_code`) <-> hồ sơ nhân sự
(`users.employee_id`), để một tài khoản trực quầy đăng nhập cũng đồng thời là
tài khoản dùng cho Giao việc/KPI (nhận việc, xem "Công việc của tôi"...).

    python -m scripts.link_goiso_users_to_employees            # dry-run, in báo cáo
    python -m scripts.link_goiso_users_to_employees --commit   # ghi users.employee_id

Nguồn dữ liệu goiso gốc CHỈ có full_name (không có mã nhân sự/ID ổn định nào
khác — xem scripts/migrate_goiso_users.py), nên đây là lần đối chiếu MỘT LẦN
bằng tên trong phạm vi đúng chi nhánh (qua goiso_branch_code ->
organization_units), không phải cơ chế đối chiếu bằng tên chạy thường xuyên.
Sau khi liên kết, các chức năng khác (Giao việc/KPI) đều dùng employee_id ổn
định, không so tên nữa.

Chỉ tự động ghi các trường hợp KHỚP TUYỆT ĐỐI (full_name trùng nguyên văn,
sau khi rút gọn khoảng trắng) và chưa có tài khoản nào khác liên kết tới nhân
sự đó. Các trường hợp khớp gần đúng (lệch dấu, thiếu từ đệm...) chỉ được IN
RA để người dùng xác nhận thủ công — KHÔNG tự ghi, tránh gán nhầm danh tính.
"""
from __future__ import annotations

import argparse
import os
import re
import unicodedata

from dotenv import load_dotenv
from sqlalchemy import text


def _norm_exact(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).casefold()


def _strip_diacritics(s: str) -> str:
    s = (s or "").replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _norm_loose(s: str) -> str:
    """Chỉ dùng để GỢI Ý — bỏ dấu thanh + gộp khoảng trắng, để phát hiện lệch
    dấu ('Thùy' vs 'Thủy') hoặc chỉ khác cách gõ, KHÔNG dùng để tự ghi."""
    return re.sub(r"\s+", " ", _strip_diacritics(s).strip()).casefold()


def _descendant_unit_ids(conn, root_id: int) -> set[int]:
    """BFS lấy toàn bộ id đơn vị con (id đơn vị là số nguyên nội bộ, không
    phải input người dùng — nối chuỗi trực tiếp vào IN(...) là an toàn)."""
    ids = {root_id}
    frontier = {root_id}
    while frontier:
        rows = conn.execute(
            text(f"SELECT id FROM organization_units WHERE parent_id IN ({','.join(map(str, frontier))})")
        ).fetchall()
        children = {r[0] for r in rows}
        new = children - ids
        if not new:
            break
        ids |= new
        frontier = new
    return ids


def run(commit: bool) -> None:
    load_dotenv()
    from app import create_app
    from app.extensions import db

    app = create_app(os.getenv("FLASK_ENV"))
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()

        candidates_users = conn.execute(text(
            "SELECT id, username, full_name, goiso_branch_code FROM users "
            "WHERE goiso_branch_code IS NOT NULL AND employee_id IS NULL"
        )).fetchall()

        already_linked_employee_ids = {
            r[0] for r in conn.execute(text(
                "SELECT employee_id FROM users WHERE employee_id IS NOT NULL"
            )).fetchall()
        }

        linked, review, unmatched, conflicts = [], [], [], []

        for u in candidates_users:
            unit_row = conn.execute(
                text("SELECT id, name FROM organization_units WHERE goiso_branch_code=:c"),
                {"c": u.goiso_branch_code},
            ).fetchone()
            if not unit_row:
                unmatched.append(f"  [{u.username}] '{u.full_name}': không tìm thấy đơn vị cho chi nhánh '{u.goiso_branch_code}'")
                continue
            unit_ids = _descendant_unit_ids(conn, unit_row.id)
            emp_rows = conn.execute(
                text(
                    "SELECT e.id, e.employee_code, e.full_name FROM employees e "
                    "JOIN employee_assignments ea ON ea.employee_id=e.id "
                    f"WHERE ea.unit_id IN ({','.join(map(str, unit_ids))}) "
                    "AND ea.end_date IS NULL AND ea.is_primary=1 AND e.is_deleted=0"
                )
            ).fetchall()

            exact = [e for e in emp_rows if _norm_exact(e.full_name) == _norm_exact(u.full_name)]
            if len(exact) == 1:
                emp = exact[0]
                if emp.id in already_linked_employee_ids:
                    conflicts.append(
                        f"  [{u.username}] '{u.full_name}' khớp {emp.employee_code} '{emp.full_name}' "
                        f"nhưng nhân sự này ĐÃ có tài khoản khác liên kết — bỏ qua, cần rà tay."
                    )
                    continue
                linked.append((u.id, u.username, u.full_name, emp.id, emp.employee_code, emp.full_name))
                already_linked_employee_ids.add(emp.id)
                if commit:
                    conn.execute(
                        text("UPDATE users SET employee_id=:eid WHERE id=:uid"),
                        {"eid": emp.id, "uid": u.id},
                    )
                continue
            if len(exact) > 1:
                conflicts.append(
                    f"  [{u.username}] '{u.full_name}': KHỚP TUYỆT ĐỐI VỚI {len(exact)} NHÂN SỰ "
                    f"({', '.join(e.employee_code for e in exact)}) — cần rà tay, không tự ghi."
                )
                continue

            loose = [e for e in emp_rows if _norm_loose(e.full_name) == _norm_loose(u.full_name)]
            if len(loose) == 1:
                emp = loose[0]
                review.append(
                    f"  [{u.username}] '{u.full_name}'  ~=?~  {emp.employee_code} '{emp.full_name}' "
                    f"(lệch dấu/cách gõ — KHÔNG tự ghi, cần xác nhận)"
                )
                continue

            # Tên goiso có thể là bản rút gọn (thiếu từ đệm, vd "Phạm Na" so với
            # "Phạm Thị Na") — chỉ GỢI Ý khi có DUY NHẤT một nhân sự chứa đủ tập
            # từ của tên goiso, tuyệt đối không tự ghi.
            u_tokens = set(_norm_loose(u.full_name).split())
            subset_matches = [
                e for e in emp_rows if u_tokens and u_tokens.issubset(set(_norm_loose(e.full_name).split()))
            ]
            if len(subset_matches) == 1:
                emp = subset_matches[0]
                review.append(
                    f"  [{u.username}] '{u.full_name}'  ~=?~  {emp.employee_code} '{emp.full_name}' "
                    f"(tên goiso thiếu từ đệm so với hồ sơ nhân sự — KHÔNG tự ghi, cần xác nhận)"
                )
                continue

            unmatched.append(
                f"  [{u.username}] '{u.full_name}': không tìm thấy nhân sự khớp trong "
                f"'{unit_row.name}' và các bộ phận trực thuộc ({len(emp_rows)} nhân sự đang hoạt động ở đó)"
            )

        if commit:
            trans.commit()
        else:
            trans.rollback()
        conn.close()

    print(f"KHỚP TUYỆT ĐỐI — {'ĐÃ GHI' if commit else 'sẽ ghi khi --commit'} ({len(linked)}):")
    for uid, uname, ufull, eid, ecode, efull in linked:
        print(f"  [{uname}] '{ufull}'  ->  {ecode} '{efull}' (employee_id={eid})")
    if review:
        print(f"\nCẦN XÁC NHẬN THỦ CÔNG — khớp gần đúng, KHÔNG tự ghi ({len(review)}):")
        print("\n".join(review))
    if conflicts:
        print(f"\nXUNG ĐỘT — KHÔNG tự ghi ({len(conflicts)}):")
        print("\n".join(conflicts))
    if unmatched:
        print(f"\nKHÔNG KHỚP ĐƯỢC AI ({len(unmatched)}):")
        print("\n".join(unmatched))
    print(f"\nTổng tài khoản goiso chưa liên kết: {len(candidates_users)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    run(ap.parse_args().commit)
