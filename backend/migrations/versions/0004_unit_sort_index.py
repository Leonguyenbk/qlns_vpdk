"""Thêm organization_units.sort_index để sắp xếp nhân sự theo cơ cấu tổ chức

Revision ID: 0004_unit_sort_index
Revises: 0003_hr_profile_fields
Create Date: 2026-09-01

`sort_index` = thứ tự duyệt cây (DFS) của đơn vị: Văn phòng tỉnh -> Ban Giám đốc ->
các phòng -> các chi nhánh (mỗi chi nhánh: Ban Giám đốc -> các bộ phận). Được tính lại
bởi `app.services.org_index.reindex_units()` sau mỗi lần import hoặc CRUD đơn vị,
hoặc thủ công: `flask --app wsgi reindex-units`.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_unit_sort_index"
down_revision = "0003_hr_profile_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("organization_units", sa.Column("sort_index", sa.Integer(), nullable=True))
    op.create_index("ix_organization_units_sort_index", "organization_units", ["sort_index"])


def downgrade():
    op.drop_index("ix_organization_units_sort_index", table_name="organization_units")
    op.drop_column("organization_units", "sort_index")
