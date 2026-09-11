"""Test sinh/đổi username theo đơn vị (app/services/username_service.py)."""
from __future__ import annotations

from app.extensions import db
from app.services.username_service import generate_username, name_slug, sync_username_for_employee


def test_name_slug_matches_established_goiso_convention():
    # Đối chiếu đúng 11 tài khoản gọi số thật đã di trú (mục tiêu: không đổi
    # cách đặt tên khi mở rộng cho toàn bộ nhân sự).
    cases = {
        "Mai Đức Giáp": "giapmd",
        "Bùi Ngọc Đức": "ducbn",
        "Mai Xuân Chiến": "chienmx",
        "Lê Văn Hưng": "hunglv",
        "Mai Thị Quỳnh Anh": "anhmtq",
        "Nguyễn Trung Sơn": "sonnt",
        "Đỗ Thị Ngọc Ngà": "ngadtn",
        "Bùi Thị Xuân": "xuanbt",
        "Nguyễn Duy Linh": "linhnd",
        "Bùi Thị Thùy Tiên": "tienbtt",
        "Phạm Na": "nap",
    }
    for full_name, expected in cases.items():
        assert name_slug(full_name) == expected


def test_generate_username_uses_group_unit_prefix_not_section(db, make_unit, make_position, make_employee):
    branch = make_unit("CN9", name="CN Chín", unit_type="BRANCH")
    branch.username_prefix = "cn9"
    section = make_unit("BP9", name="Bộ phận 9", unit_type="SECTION", parent=branch)
    pos = make_position("CV")
    emp = make_employee("NVX", section, pos, full_name="Trần Văn Long")
    db.session.commit()

    current = emp.primary_active_assignment()
    username = generate_username(current.employee.full_name, current.unit)
    assert username == "cn9.longtv"


def test_generate_username_avoids_collision(db, make_unit, make_position, make_employee, make_user):
    branch = make_unit("CN10", name="CN Mười", unit_type="BRANCH")
    branch.username_prefix = "cn10"
    pos = make_position("CV2")
    emp = make_employee("NVY", branch, pos, full_name="Trần Văn Long")
    db.session.commit()
    make_user("cn10.longtv", employee=None)  # đã có người khác chiếm đúng username sinh ra đầu tiên

    current = emp.primary_active_assignment()
    username = generate_username(current.employee.full_name, current.unit)
    assert username == "cn10.longtv2"


def test_generate_username_none_without_prefix(db, make_unit, make_position, make_employee):
    branch = make_unit("CN11", name="CN Mười Một", unit_type="BRANCH")  # không set username_prefix
    pos = make_position("CV3")
    emp = make_employee("NVZ", branch, pos, full_name="Trần Văn Long")
    db.session.commit()
    current = emp.primary_active_assignment()
    assert generate_username(current.employee.full_name, current.unit) is None


def test_sync_username_on_transfer_changes_prefix_only_when_group_unit_changes(
    db, make_unit, make_position, make_employee, make_user
):
    branch_a = make_unit("CNA", name="CN A", unit_type="BRANCH")
    branch_a.username_prefix = "cna"
    section_a1 = make_unit("BPA1", name="Bộ phận A1", unit_type="SECTION", parent=branch_a)
    section_a2 = make_unit("BPA2", name="Bộ phận A2", unit_type="SECTION", parent=branch_a)
    branch_b = make_unit("CNB", name="CN B", unit_type="BRANCH")
    branch_b.username_prefix = "cnb"
    pos = make_position("CV4")
    emp = make_employee("NVW", section_a1, pos, full_name="Trần Văn Long")
    db.session.commit()
    user = make_user("cna.longtv", employee=emp, full_name="Trần Văn Long")

    # Chuyển bộ phận NHƯNG VẪN trong cùng Chi nhánh -> KHÔNG đổi username
    current = emp.primary_active_assignment()
    current.unit_id = section_a2.id
    db.session.commit()
    result = sync_username_for_employee(emp, actor_id=None)
    assert result is None
    assert user.username == "cna.longtv"

    # Chuyển sang Chi nhánh khác -> ĐỔI username theo tiền tố mới
    current.unit_id = branch_b.id
    db.session.commit()
    result = sync_username_for_employee(emp, actor_id=None)
    assert result == {"old_username": "cna.longtv", "new_username": "cnb.longtv"}
    assert user.username == "cnb.longtv"
