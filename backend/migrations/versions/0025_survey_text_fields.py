"""Câu hỏi nhiều ô nhập (text_fields): mỗi ô có cờ bắt buộc riêng

Revision ID: 0025_survey_text_fields
Revises: 0024_survey_id_number
Create Date: 2026-09-21

Ô nhập của câu hỏi `text_fields` được lưu như một dòng survey_options (nhãn ô =
option_text). Thêm cột is_required để từng ô bật/tắt bắt buộc. Các phương án
của câu hỏi chọn giữ mặc định false, không ảnh hưởng hành vi hiện có.

Idempotent — chỉ thêm/xóa cột nếu (chưa/đang) tồn tại.
"""
import sqlalchemy as sa
from alembic import op

revision = "0025_survey_text_fields"
down_revision = "0024_survey_id_number"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_options")}
    if "is_required" not in columns:
        with op.batch_alter_table("survey_options") as batch:
            batch.add_column(
                sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false())
            )


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_options")}
    if "is_required" in columns:
        with op.batch_alter_table("survey_options") as batch:
            batch.drop_column("is_required")
