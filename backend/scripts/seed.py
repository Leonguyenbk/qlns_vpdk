"""Seed dữ liệu mẫu: đơn vị, chức vụ, giới hạn chức vụ, nhân sự và tài khoản mẫu.

Chạy:
    python -m scripts.seed
hoặc:
    flask --app wsgi seed

Idempotent: nếu đã seed (tồn tại đơn vị mã 'HO') thì bỏ qua.
"""
from __future__ import annotations

import os
from datetime import date

from dotenv import load_dotenv


def run_seed() -> None:
    load_dotenv()
    from app import create_app
    from app.extensions import db
    from app.models import (
        Employee,
        EmployeeAssignment,
        OrganizationUnit,
        Position,
        Role,
        UnitPositionLimit,
        User,
        UserUnitScope,
    )
    from app.permissions.constants import (
        ROLE_HR_ADMIN,
        ROLE_UNIT_MANAGER,
        ROLE_VIEWER,
    )

    app = create_app(os.getenv("FLASK_ENV"))
    with app.app_context():
        if db.session.query(OrganizationUnit).filter_by(code="HO").first():
            print("Dữ liệu mẫu đã tồn tại, bỏ qua seed.")
            return

        # ---------------- Đơn vị ----------------
        head = OrganizationUnit(
            code="HO", name="Trụ sở chính", unit_type="HEAD_OFFICE",
            address="Số 1 Đại lộ Trung tâm", phone="02400000000", email="ho@example.com",
        )
        db.session.add(head)
        db.session.flush()

        departments = []
        for code, name in [
            ("P-TCNS", "Phòng Tổ chức - Nhân sự"),
            ("P-KT", "Phòng Kế toán"),
            ("P-KD", "Phòng Kinh doanh"),
            ("P-CNTT", "Phòng Công nghệ thông tin"),
            ("P-HC", "Phòng Hành chính"),
        ]:
            d = OrganizationUnit(
                code=code, name=name, unit_type="DEPARTMENT", parent_id=head.id,
                email=f"{code.lower()}@example.com",
            )
            db.session.add(d)
            departments.append(d)
        db.session.flush()

        branches = []
        for i in range(1, 25):
            b = OrganizationUnit(
                code=f"CN{i:02d}",
                name=f"Chi nhánh {i:02d}",
                unit_type="BRANCH",
                parent_id=head.id,
                address=f"Địa chỉ chi nhánh {i:02d}",
                phone=f"024{i:07d}",
                email=f"cn{i:02d}@example.com",
            )
            db.session.add(b)
            branches.append(b)
        db.session.flush()

        # Một số bộ phận trực thuộc chi nhánh đầu tiên
        sections = []
        for code, name in [("KD", "Bộ phận Kinh doanh"), ("KT", "Bộ phận Kế toán"), ("GD", "Bộ phận Giao dịch")]:
            s = OrganizationUnit(
                code=f"CN01-{code}", name=f"{name} - Chi nhánh 01",
                unit_type="SECTION", parent_id=branches[0].id,
            )
            db.session.add(s)
            sections.append(s)
        db.session.flush()

        # ---------------- Chức vụ ----------------
        positions_data = [
            ("TGD", "Tổng giám đốc", 100, True),
            ("PTGD", "Phó tổng giám đốc", 90, True),
            ("GDCN", "Giám đốc chi nhánh", 80, True),
            ("PGDCN", "Phó giám đốc chi nhánh", 70, True),
            ("TP", "Trưởng phòng", 60, True),
            ("PP", "Phó trưởng phòng", 50, True),
            ("TBP", "Trưởng bộ phận", 40, True),
            ("CV", "Chuyên viên", 20, False),
            ("NV", "Nhân viên", 10, False),
        ]
        positions = {}
        for code, name, level, managerial in positions_data:
            p = Position(code=code, name=name, level=level, is_managerial=managerial)
            db.session.add(p)
            positions[code] = p
        db.session.flush()

        # ---------------- Giới hạn chức vụ ----------------
        limits = []
        # Trụ sở: 1 TGD, 3 PTGD
        limits.append(UnitPositionLimit(unit_id=head.id, position_id=positions["TGD"].id, max_holders=1))
        limits.append(UnitPositionLimit(unit_id=head.id, position_id=positions["PTGD"].id, max_holders=3))
        # Mỗi phòng: 1 TP, 2 PP
        for d in departments:
            limits.append(UnitPositionLimit(unit_id=d.id, position_id=positions["TP"].id, max_holders=1))
            limits.append(UnitPositionLimit(unit_id=d.id, position_id=positions["PP"].id, max_holders=2))
        # Mỗi chi nhánh: 1 GĐCN, 2 PGĐCN
        for b in branches:
            limits.append(UnitPositionLimit(unit_id=b.id, position_id=positions["GDCN"].id, max_holders=1))
            limits.append(UnitPositionLimit(unit_id=b.id, position_id=positions["PGDCN"].id, max_holders=2))
        # Mỗi bộ phận: 1 TBP
        for s in sections:
            limits.append(UnitPositionLimit(unit_id=s.id, position_id=positions["TBP"].id, max_holders=1))
        db.session.add_all(limits)
        db.session.flush()

        # ---------------- Nhân sự + phân công ----------------
        def make_employee(code, name, dob, gender, unit, pos_code, atype, start, cccd=None):
            emp = Employee(
                employee_code=code,
                full_name=name,
                date_of_birth=dob,
                gender=gender,
                identity_number=cccd,
                phone="0900000000",
                email=f"{code.lower()}@example.com",
                employment_type="OFFICIAL",
                professional_title="Cử nhân",
                recruitment_date=start,
                status="WORKING",
            )
            db.session.add(emp)
            db.session.flush()
            db.session.add(
                EmployeeAssignment(
                    employee_id=emp.id,
                    unit_id=unit.id,
                    position_id=positions[pos_code].id,
                    assignment_type=atype,
                    start_date=start,
                    is_primary=True,
                    decision_number=f"QD-{code}",
                    decision_date=start,
                )
            )
            return emp

        make_employee("NS0001", "Nguyễn Văn An", date(1975, 5, 20), "MALE", head, "TGD", "APPOINTMENT", date(2015, 1, 1), "012345678901")
        make_employee("NS0002", "Trần Thị Bình", date(1980, 3, 12), "FEMALE", head, "PTGD", "APPOINTMENT", date(2016, 6, 1), "012345678902")
        make_employee("NS0003", "Lê Văn Cường", date(1982, 8, 8), "MALE", departments[0], "TP", "APPOINTMENT", date(2017, 2, 1), "012345678903")
        make_employee("NS0004", "Phạm Thị Dung", date(1988, 11, 2), "FEMALE", departments[0], "CV", "RECRUITMENT", date(2019, 3, 15))
        make_employee("NS0005", "Hoàng Văn Em", date(1990, 1, 25), "MALE", departments[2], "TP", "APPOINTMENT", date(2018, 9, 1), "012345678905")
        make_employee("NS0006", "Vũ Thị Gấm", date(1992, 7, 7), "FEMALE", departments[2], "CV", "RECRUITMENT", date(2020, 1, 6))
        make_employee("NS0007", "Đỗ Văn Hùng", date(1979, 4, 18), "MALE", branches[0], "GDCN", "APPOINTMENT", date(2016, 5, 1), "012345678907")
        make_employee("NS0008", "Bùi Thị Hoa", date(1985, 9, 30), "FEMALE", branches[0], "PGDCN", "APPOINTMENT", date(2018, 1, 1))
        make_employee("NS0009", "Đinh Văn Khoa", date(1993, 2, 14), "MALE", sections[0], "TBP", "APPOINTMENT", date(2021, 4, 1))
        make_employee("NS0010", "Ngô Thị Lan", date(1995, 6, 21), "FEMALE", sections[0], "NV", "RECRUITMENT", date(2022, 8, 1))
        make_employee("NS0011", "Dương Văn Minh", date(1987, 12, 5), "MALE", branches[1], "GDCN", "APPOINTMENT", date(2019, 7, 1))
        make_employee("NS0012", "Lý Thị Nga", date(1991, 10, 10), "FEMALE", branches[1], "CV", "RECRUITMENT", date(2021, 2, 1))
        make_employee("NS0013", "Phan Văn Oanh", date(1994, 3, 3), "MALE", branches[2], "GDCN", "APPOINTMENT", date(2020, 11, 1))
        make_employee("NS0014", "Tạ Thị Phương", date(1996, 5, 16), "FEMALE", departments[1], "TP", "APPOINTMENT", date(2019, 1, 2))
        make_employee("NS0015", "Chu Văn Quang", date(1998, 8, 28), "MALE", departments[3], "TP", "APPOINTMENT", date(2020, 3, 2))
        db.session.flush()

        # ---------------- Tài khoản mẫu ----------------
        def make_user(username, full_name, role_code, scopes):
            role = db.session.query(Role).filter_by(code=role_code).first()
            u = User(username=username, full_name=full_name, email=f"{username}@example.com", is_active=True)
            u.set_password("Password@123")
            u.roles.append(role)
            for stype, unit_code in scopes:
                unit_id = None
                if unit_code:
                    unit_id = db.session.query(OrganizationUnit).filter_by(code=unit_code).first().id
                u.unit_scopes.append(UserUnitScope(scope_type=stype, unit_id=unit_id))
            db.session.add(u)

        make_user("hradmin", "Quản trị nhân sự", ROLE_HR_ADMIN, [("GLOBAL", None)])
        make_user("cn01manager", "Quản lý Chi nhánh 01", ROLE_UNIT_MANAGER, [("SUBTREE", "CN01")])
        make_user("viewer", "Người xem", ROLE_VIEWER, [("GLOBAL", None)])

        db.session.commit()

        print("Seed hoàn tất:")
        print(f"  - {db.session.query(OrganizationUnit).count()} đơn vị")
        print(f"  - {db.session.query(Position).count()} chức vụ")
        print(f"  - {db.session.query(UnitPositionLimit).count()} cấu hình giới hạn chức vụ")
        print(f"  - {db.session.query(Employee).count()} nhân sự")
        print("  - Tài khoản mẫu (mật khẩu: Password@123): hradmin, cn01manager, viewer")


if __name__ == "__main__":
    run_seed()
