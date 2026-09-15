"""Thêm survey_questions.section — nhóm câu hỏi theo "Phần" khi hiển thị/báo cáo

Revision ID: 0016_survey_question_sections
Revises: 0015_survey_branch_limits
Create Date: 2026-09-15

Chỉ thêm 1 cột nullable, không đụng dữ liệu hiện có. Idempotent (kiểm tra cột
đã tồn tại trước khi thêm).
"""
from alembic import op
import sqlalchemy as sa

revision = "0016_survey_question_sections"
down_revision = "0015_survey_branch_limits"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("survey_questions")}
    if "section" not in cols:
        op.add_column("survey_questions", sa.Column("section", sa.String(length=255), nullable=True))


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("survey_questions")}
    if "section" in cols:
        op.drop_column("survey_questions", "section")
