"""Model hồ sơ nhân sự và lịch sử phân công công tác."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


class Employee(TimestampMixin, db.Model):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("employee_code", name="uq_employees_code"),
        Index("ix_employees_full_name", "full_name"),
        Index("ix_employees_status", "status"),
        Index("ix_employees_is_deleted", "is_deleted"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(10))
    identity_number: Mapped[str | None] = mapped_column(String(30))
    phone: Mapped[str | None] = mapped_column(String(20), index=True)
    email: Mapped[str | None] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(String(255))
    professional_title: Mapped[str | None] = mapped_column(String(150))
    employment_type: Mapped[str | None] = mapped_column(String(20))
    recruitment_date: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(20), default="WORKING", nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Hồ sơ mở rộng (nguồn: biểu thống kê viên chức / NLĐ "Phụ lục 4") ---
    place_of_origin: Mapped[str | None] = mapped_column(String(255))       # Quê quán
    identity_issued_date: Mapped[date | None] = mapped_column(Date)        # Ngày cấp CCCD
    identity_issued_place: Mapped[str | None] = mapped_column(String(255))  # Nơi cấp CCCD
    job_grade_code: Mapped[str | None] = mapped_column(String(30), index=True)  # Ngạch/CDNN (mã)
    job_grade_name: Mapped[str | None] = mapped_column(String(150))        # Tên ngạch
    job_duties: Mapped[str | None] = mapped_column(Text)                   # Nhiệm vụ đang đảm nhận
    tenure_date: Mapped[date | None] = mapped_column(Date)                 # Ngày vào biên chế
    contract_type: Mapped[str | None] = mapped_column(String(50))         # Loại hợp đồng (gốc)
    education_level: Mapped[str | None] = mapped_column(String(20))        # Trình độ cao nhất
    education_major: Mapped[str | None] = mapped_column(String(255))      # Ngành đào tạo (cao nhất)
    education_mode: Mapped[str | None] = mapped_column(String(50))        # Hệ đào tạo (cao nhất)
    foreign_language_cert: Mapped[str | None] = mapped_column(String(100))  # Chứng chỉ ngoại ngữ
    it_cert: Mapped[str | None] = mapped_column(String(100))              # Chứng chỉ tin học

    assignments: Mapped[list["EmployeeAssignment"]] = relationship(
        "EmployeeAssignment",
        back_populates="employee",
        order_by="EmployeeAssignment.start_date.desc()",
    )
    education: Mapped[list["EmployeeEducation"]] = relationship(
        "EmployeeEducation",
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="EmployeeEducation.is_highest.desc()",
    )

    # --- Đơn vị / chức vụ hiện tại lấy từ phân công chính đang hiệu lực ---
    def primary_active_assignment(self) -> "EmployeeAssignment | None":
        for a in self.assignments:
            if a.is_primary and a.end_date is None:
                return a
        return None

    def to_dict(self, *, include_sensitive: bool = False, include_current: bool = True) -> dict:
        data = {
            "id": self.id,
            "employee_code": self.employee_code,
            "full_name": self.full_name,
            "date_of_birth": _iso(self.date_of_birth),
            "gender": self.gender,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "professional_title": self.professional_title,
            "employment_type": self.employment_type,
            "recruitment_date": _iso(self.recruitment_date),
            "status": self.status,
            "avatar_url": self.avatar_url,
            "notes": self.notes,
            "is_deleted": self.is_deleted,
            "deleted_at": _iso(self.deleted_at),
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
            # Hồ sơ mở rộng
            "place_of_origin": self.place_of_origin,
            "identity_issued_date": _iso(self.identity_issued_date),
            "identity_issued_place": self.identity_issued_place,
            "job_grade_code": self.job_grade_code,
            "job_grade_name": self.job_grade_name,
            "job_duties": self.job_duties,
            "tenure_date": _iso(self.tenure_date),
            "contract_type": self.contract_type,
            "education_level": self.education_level,
            "education_major": self.education_major,
            "education_mode": self.education_mode,
            "foreign_language_cert": self.foreign_language_cert,
            "it_cert": self.it_cert,
        }
        # Trường nhạy cảm chỉ hiển thị khi có quyền employee.view_sensitive
        data["identity_number"] = self.identity_number if include_sensitive else None
        data["has_sensitive_data"] = bool(self.identity_number)

        if include_current:
            current = self.primary_active_assignment()
            if current:
                data["current_unit"] = (
                    {
                        "id": current.unit.id,
                        "code": current.unit.code,
                        "name": current.unit.name,
                        "path": current.unit.display_path,
                        "group_name": current.unit.group_name,   # cột Phòng / Chi nhánh
                        "section_name": current.unit.section_name,  # cột Bộ phận (có thể null)
                    }
                    if current.unit
                    else None
                )
                data["current_position"] = (
                    {
                        "id": current.position.id,
                        "code": current.position.code,
                        "name": current.position.name,
                    }
                    if current.position
                    else None
                )
                data["current_assignment_id"] = current.id
            else:
                data["current_unit"] = None
                data["current_position"] = None
                data["current_assignment_id"] = None
        return data


class EmployeeAssignment(TimestampMixin, db.Model):
    """Lịch sử phân công / quá trình công tác của nhân sự."""

    __tablename__ = "employee_assignments"
    __table_args__ = (
        Index("ix_assignment_employee_primary", "employee_id", "is_primary", "end_date"),
        Index("ix_assignment_unit", "unit_id"),
        Index("ix_assignment_position", "position_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("organization_units.id", ondelete="RESTRICT"), nullable=False
    )
    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id", ondelete="RESTRICT"), nullable=False
    )
    assignment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    decision_number: Mapped[str | None] = mapped_column(String(100))
    decision_date: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="assignments")
    unit = relationship("OrganizationUnit")
    position = relationship("Position")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "unit_id": self.unit_id,
            "position_id": self.position_id,
            "assignment_type": self.assignment_type,
            "start_date": _iso(self.start_date),
            "end_date": _iso(self.end_date),
            "is_primary": self.is_primary,
            "is_active": self.end_date is None,
            "decision_number": self.decision_number,
            "decision_date": _iso(self.decision_date),
            "note": self.note,
            "created_by": self.created_by,
            "unit": {
                "id": self.unit.id,
                "code": self.unit.code,
                "name": self.unit.name,
                "path": self.unit.display_path,
                "group_name": self.unit.group_name,
                "section_name": self.unit.section_name,
            }
            if self.unit
            else None,
            "position": {
                "id": self.position.id,
                "code": self.position.code,
                "name": self.position.name,
            }
            if self.position
            else None,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }


class EmployeeEducation(TimestampMixin, db.Model):
    """Bằng cấp / trình độ đào tạo của nhân sự (một người có thể nhiều bằng)."""

    __tablename__ = "employee_education"
    __table_args__ = (Index("ix_employee_education_employee_id", "employee_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level: Mapped[str | None] = mapped_column(String(20))       # ĐH / Ths / CĐ / TC / TS
    major: Mapped[str | None] = mapped_column(String(255))      # Ngành đào tạo
    mode: Mapped[str | None] = mapped_column(String(50))        # Hệ: Chính quy / VLVH / Từ xa
    institution: Mapped[str | None] = mapped_column(String(255))
    is_highest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="education")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "level": self.level,
            "major": self.major,
            "mode": self.mode,
            "institution": self.institution,
            "is_highest": self.is_highest,
        }


class JobGrade(TimestampMixin, db.Model):
    """Danh mục ngạch / chức danh nghề nghiệp (mã -> tên). Import tự tạo mã mới, tên có thể bổ sung sau."""

    __tablename__ = "job_grades"
    __table_args__ = (UniqueConstraint("code", name="uq_job_grades_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(150))
    category: Mapped[str | None] = mapped_column(String(30))  # "Viên chức" / "Hợp đồng"

    def to_dict(self) -> dict:
        return {"id": self.id, "code": self.code, "name": self.name, "category": self.category}
