"""Cờ công khai bảng xếp hạng khảo sát (chỉ thứ hạng/điểm, không chi tiết câu hỏi)

Revision ID: 0026_survey_results_public
Revises: 0025_survey_text_fields
Create Date: 2026-09-24

Người tạo khảo sát/admin bật cờ này để công khai trang xếp hạng theo chi
nhánh (điểm trung bình + thứ hạng) tại /ket-qua-khao-sat/<slug>. Không lộ
câu trả lời/điểm từng câu hỏi. Mặc định tắt.

Idempotent — chỉ thêm/xóa cột nếu (chưa/đang) tồn tại.
"""
import sqlalchemy as sa
from alembic import op

revision = "0026_survey_results_public"
down_revision = "0025_survey_text_fields"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("surveys")}
    if "is_results_public" not in columns:
        with op.batch_alter_table("surveys") as batch:
            batch.add_column(
                sa.Column("is_results_public", sa.Boolean(), nullable=False, server_default=sa.false())
            )


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("surveys")}
    if "is_results_public" in columns:
        with op.batch_alter_table("surveys") as batch:
            batch.drop_column("is_results_public")
