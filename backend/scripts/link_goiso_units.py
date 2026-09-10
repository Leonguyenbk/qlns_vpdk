"""Liên kết organization_units (nhân sự) <-> chi nhánh goiso.

    python -m scripts.link_goiso_units            # dry-run, in bảng đối chiếu
    python -m scripts.link_goiso_units --commit   # ghi organization_units.goiso_branch_code

Khớp theo TÊN đã chuẩn hoá: bỏ tiền tố "CN "/"Chi nhánh ", bỏ dấu, bỏ ký tự
không phải chữ/số, gộp khoảng trắng. (mã goiso 'bmt' <-> đơn vị 'CN Buôn Ma Thuột'.)
"""
from __future__ import annotations

import argparse
import os
import re
import unicodedata

from dotenv import load_dotenv
from sqlalchemy import text


def _norm(s: str) -> str:
    s = (s or "").replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"^(cn|chi nhanh|chi nhánh|chi-nhanh)\s+", "", s.strip())
    s = re.sub(r"^(khu vuc|khu vực)\s+", "", s)
    s = s.replace("'", "").replace("’", "")  # M'gar / M'Drắk -> Mgar / MDrak
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def run(commit: bool) -> None:
    load_dotenv()
    from app import create_app
    from app.extensions import db

    app = create_app(os.getenv("FLASK_ENV"))
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        branches = list(
            conn.execute(text("SELECT id, code, name, full_name FROM goiso_branches"))
        )
        units = list(
            conn.execute(
                text(
                    "SELECT id, code, name, goiso_branch_code FROM organization_units "
                    "WHERE unit_type='BRANCH'"
                )
            )
        )
        b_by_norm = {}
        for b in branches:
            b_by_norm.setdefault(_norm(b.name), b)
            b_by_norm.setdefault(_norm(b.full_name), b)

        matched, changed, unmatched_units = [], 0, []
        used_codes = set()
        for u in units:
            b = b_by_norm.get(_norm(u.name))
            if not b:
                unmatched_units.append(u.name)
                continue
            used_codes.add(b.code)
            matched.append(f"  {u.name:28s} <->  {b.code:10s} {b.name}")
            if u.goiso_branch_code != b.code:
                conn.execute(
                    text(
                        "UPDATE organization_units SET goiso_branch_code=:c WHERE id=:i"
                    ),
                    {"c": b.code, "i": u.id},
                )
                changed += 1

        unmatched_branches = [f"{b.code} ({b.name})" for b in branches if b.code not in used_codes]

        if commit:
            trans.commit()
        else:
            trans.rollback()
        conn.close()

    print("KHỚP:")
    print("\n".join(matched) or "  (không)")
    if unmatched_units:
        print(f"\nĐơn vị BRANCH không khớp chi nhánh goiso ({len(unmatched_units)}):")
        print("  " + ", ".join(unmatched_units))
    if unmatched_branches:
        print(f"\nChi nhánh goiso không có đơn vị tương ứng ({len(unmatched_branches)}):")
        print("  " + ", ".join(unmatched_branches))
    print(
        f"\nĐơn vị khớp: {len(matched)}  |  cập nhật goiso_branch_code: {changed}  "
        f"({'ĐÃ GHI' if commit else 'dry-run — thêm --commit'})"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    run(ap.parse_args().commit)
