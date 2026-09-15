"""Thông tin liên hệ người khảo sát: email, địa chỉ

Revision ID: 0013_survey_respondent_contact
Revises: 0012_survey_editor_role
Create Date: 2026-09-15

Trang khảo sát công khai từ nay luôn hỏi 2 mục mặc định: (1) Chi nhánh được
khảo sát — tự chọn sẵn khi quét mã QR dán tại chi nhánh, đỡ phải chọn tay —
và (2) thông tin liên hệ người khảo sát (họ tên, SĐT, email, địa chỉ — đều
không bắt buộc). Chi nhánh (branch_id) và họ tên/SĐT đã có sẵn từ trước;
migration này chỉ bổ sung 2 cột còn thiếu: email và địa chỉ.

Idempotent — chỉ thêm cột nếu chưa có.
"""
import sqlalchemy as sa
from alembic import op

revision = "0013_survey_respondent_contact"
down_revision = "0012_survey_editor_role"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("survey_responses")}
    if "respondent_email" not in cols:
        op.add_column("survey_responses", sa.Column("respondent_email", sa.String(length=120), nullable=True))
    if "respondent_address" not in cols:
        op.add_column("survey_responses", sa.Column("respondent_address", sa.String(length=255), nullable=True))


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("survey_responses")}
    if "respondent_address" in cols:
        op.drop_column("survey_responses", "respondent_address")
    if "respondent_email" in cols:
        op.drop_column("survey_responses", "respondent_email")
