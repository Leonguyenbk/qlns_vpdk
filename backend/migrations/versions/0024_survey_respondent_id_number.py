"""Thay Email bằng số CCCD/CMND ở thông tin liên hệ người khảo sát

Revision ID: 0024_survey_id_number
Revises: 0023_survey_conditions
Create Date: 2026-09-18

Bỏ thu thập email (theo yêu cầu, không giữ lại dữ liệu email cũ). Thêm
respondent_id_number: CCCD 12 số (được phép có số 0 đầu) hoặc CMND 9 số —
bắt buộc nhập cùng họ tên/SĐT khi khảo sát không ẩn danh.

Idempotent — chỉ thêm/xóa cột nếu (chưa/đang) tồn tại.
"""
import sqlalchemy as sa
from alembic import op

revision = "0024_survey_id_number"
down_revision = "0023_survey_conditions"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_responses")}
    with op.batch_alter_table("survey_responses") as batch:
        if "respondent_id_number" not in columns:
            batch.add_column(sa.Column("respondent_id_number", sa.String(length=12), nullable=True))
        if "respondent_email" in columns:
            batch.drop_column("respondent_email")


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_responses")}
    with op.batch_alter_table("survey_responses") as batch:
        if "respondent_email" not in columns:
            batch.add_column(sa.Column("respondent_email", sa.String(length=120), nullable=True))
        if "respondent_id_number" in columns:
            batch.drop_column("respondent_id_number")
