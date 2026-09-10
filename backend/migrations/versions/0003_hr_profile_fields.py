"""Bổ sung trường hồ sơ nhân sự cho nhập liệu từ "Phụ lục 4"

Revision ID: 0003_hr_profile_fields
Revises: 0002_seed_roles_permissions
Create Date: 2026-09-01

Thêm vào bảng employees các trường có trong biểu mẫu thống kê viên chức / NLĐ:
  - place_of_origin        : Quê quán
  - identity_issued_date   : Ngày cấp CCCD
  - identity_issued_place   : Nơi cấp CCCD
  - job_grade_code          : Ngạch / Chức danh nghề nghiệp (mã, vd V.06.01.02)
  - job_grade_name          : Tên ngạch (điền từ bảng job_grades nếu có)
  - job_duties              : Các nhiệm vụ đang đảm nhận
  - tenure_date             : Ngày vào biên chế (khác recruitment_date = ngày tuyển dụng/HĐLĐ)
  - contract_type           : Loại hợp đồng (giá trị gốc: "Viên chức" / "KXĐTH" / "HĐLĐ 12 tháng"...)
  - education_level/major/mode : Trình độ / Ngành / Hệ đào tạo CAO NHẤT (bản rút gọn để lọc & hiển thị)
  - foreign_language_cert   : Chứng chỉ ngoại ngữ
  - it_cert                 : Chứng chỉ tin học

Bảng mới:
  - employee_education : toàn bộ các bằng cấp của một người (người có "Ths, ĐH")
  - job_grades         : danh mục ngạch / CDNN (code -> name)
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_hr_profile_fields"
down_revision = "0002_seed_roles_permissions"
branch_labels = None
depends_on = None

MYSQL_ARGS = {"mysql_charset": "utf8mb4", "mysql_engine": "InnoDB"}

_NEW_COLUMNS = [
    ("place_of_origin", sa.String(length=255)),
    ("identity_issued_date", sa.Date()),
    ("identity_issued_place", sa.String(length=255)),
    ("job_grade_code", sa.String(length=30)),
    ("job_grade_name", sa.String(length=150)),
    ("job_duties", sa.Text()),
    ("tenure_date", sa.Date()),
    ("contract_type", sa.String(length=50)),
    ("education_level", sa.String(length=20)),
    ("education_major", sa.String(length=255)),
    ("education_mode", sa.String(length=50)),
    ("foreign_language_cert", sa.String(length=100)),
    ("it_cert", sa.String(length=100)),
]


def upgrade():
    for name, coltype in _NEW_COLUMNS:
        op.add_column("employees", sa.Column(name, coltype, nullable=True))
    op.create_index("ix_employees_job_grade_code", "employees", ["job_grade_code"])

    op.create_table(
        "job_grades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=True),
        sa.Column("category", sa.String(length=30), nullable=True),  # "Viên chức" / "Hợp đồng"
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_job_grades_code"),
        **MYSQL_ARGS,
    )

    op.create_table(
        "employee_education",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=True),   # ĐH / Ths / CĐ / TC / TS
        sa.Column("major", sa.String(length=255), nullable=True),  # Ngành đào tạo
        sa.Column("mode", sa.String(length=50), nullable=True),    # Hệ: Chính quy / VLVH / Từ xa
        sa.Column("institution", sa.String(length=255), nullable=True),
        sa.Column("is_highest", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        **MYSQL_ARGS,
    )
    op.create_index("ix_employee_education_employee_id", "employee_education", ["employee_id"])


def downgrade():
    op.drop_table("employee_education")
    op.drop_table("job_grades")
    op.drop_index("ix_employees_job_grade_code", table_name="employees")
    for name, _ in reversed(_NEW_COLUMNS):
        op.drop_column("employees", name)
