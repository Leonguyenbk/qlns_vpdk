"""Câu hỏi phụ có điều kiện và chế độ chấm điểm trừ.

Revision ID: 0023_survey_conditions
Revises: 0022_survey_sections_scores
Create Date: 2026-09-18
"""
import sqlalchemy as sa
from alembic import op


revision = "0023_survey_conditions"
down_revision = "0022_survey_sections_scores"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_questions")}
    with op.batch_alter_table("survey_questions") as batch:
        if "scoring_mode" not in columns:
            batch.add_column(
                sa.Column("scoring_mode", sa.String(length=20), nullable=False, server_default="standard")
            )
        if "max_score" not in columns:
            batch.add_column(sa.Column("max_score", sa.Float(), nullable=True))
        if "zero_score_at" not in columns:
            batch.add_column(sa.Column("zero_score_at", sa.Integer(), nullable=True))
        if "parent_question_id" not in columns:
            batch.add_column(sa.Column("parent_question_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                "fk_survey_questions_parent_question_id",
                "survey_questions",
                ["parent_question_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch.create_index("ix_survey_questions_parent_question_id", ["parent_question_id"])
        if "trigger_option_id" not in columns:
            batch.add_column(sa.Column("trigger_option_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                "fk_survey_questions_trigger_option_id",
                "survey_options",
                ["trigger_option_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch.create_index("ix_survey_questions_trigger_option_id", ["trigger_option_id"])
        if "trigger_answer" not in columns:
            batch.add_column(sa.Column("trigger_answer", sa.String(length=20), nullable=True))

    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_answers")}
    with op.batch_alter_table("survey_answers") as batch:
        if "score_recorded" not in columns:
            batch.add_column(sa.Column("score_recorded", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "earned_score" not in columns:
            batch.add_column(sa.Column("earned_score", sa.Float(), nullable=True))
        if "score_in_total" not in columns:
            batch.add_column(sa.Column("score_in_total", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_answers")}
    with op.batch_alter_table("survey_answers") as batch:
        for name in ("score_in_total", "earned_score", "score_recorded"):
            if name in columns:
                batch.drop_column(name)
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_questions")}
    with op.batch_alter_table("survey_questions") as batch:
        if "trigger_answer" in columns:
            batch.drop_column("trigger_answer")
        if "trigger_option_id" in columns:
            batch.drop_index("ix_survey_questions_trigger_option_id")
            batch.drop_constraint("fk_survey_questions_trigger_option_id", type_="foreignkey")
            batch.drop_column("trigger_option_id")
        if "parent_question_id" in columns:
            batch.drop_index("ix_survey_questions_parent_question_id")
            batch.drop_constraint("fk_survey_questions_parent_question_id", type_="foreignkey")
            batch.drop_column("parent_question_id")
        if "zero_score_at" in columns:
            batch.drop_column("zero_score_at")
        if "max_score" in columns:
            batch.drop_column("max_score")
        if "scoring_mode" in columns:
            batch.drop_column("scoring_mode")
