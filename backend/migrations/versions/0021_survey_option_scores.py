"""Thêm điểm cho từng phương án trả lời khảo sát.

Revision ID: 0021_survey_option_scores
Revises: 0020_announcements
Create Date: 2026-09-18
"""
import sqlalchemy as sa
from alembic import op


revision = "0021_survey_option_scores"
down_revision = "0020_announcements"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_options")}
    if "score" not in columns:
        op.add_column("survey_options", sa.Column("score", sa.Float(), nullable=True))


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_options")}
    if "score" in columns:
        op.drop_column("survey_options", "score")
