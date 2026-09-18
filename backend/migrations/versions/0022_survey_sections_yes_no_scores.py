"""Danh mục phần khảo sát và điểm cho đáp án Có/Không.

Revision ID: 0022_survey_sections_scores
Revises: 0021_survey_option_scores
Create Date: 2026-09-18
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = "0022_survey_sections_scores"
down_revision = "0021_survey_option_scores"
branch_labels = None
depends_on = None

MYSQL_ARGS = {"mysql_charset": "utf8mb4", "mysql_engine": "InnoDB"}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "survey_sections" not in tables:
        op.create_table(
            "survey_sections",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("survey_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("survey_id", "title", name="uq_survey_sections_title"),
            **MYSQL_ARGS,
        )
        op.create_index(
            "ix_survey_sections_order", "survey_sections", ["survey_id", "sort_order"]
        )

    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_questions")}
    with op.batch_alter_table("survey_questions") as batch:
        if "section_id" not in columns:
            batch.add_column(sa.Column("section_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                "fk_survey_questions_section_id",
                "survey_sections",
                ["section_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch.create_index("ix_survey_questions_section_id", ["section_id"])
        if "yes_score" not in columns:
            batch.add_column(sa.Column("yes_score", sa.Float(), nullable=True))
        if "no_score" not in columns:
            batch.add_column(sa.Column("no_score", sa.Float(), nullable=True))

    # Chuyển các nhãn "Phần" cũ thành danh mục riêng, không làm mất khảo sát hiện có.
    rows = bind.execute(
        sa.text(
            "SELECT DISTINCT survey_id, section FROM survey_questions "
            "WHERE section IS NOT NULL AND TRIM(section) <> '' ORDER BY survey_id, section"
        )
    ).fetchall()
    order_by_survey: dict[int, int] = {}
    now = datetime.now(timezone.utc)
    for survey_id, title in rows:
        existing = bind.execute(
            sa.text(
                "SELECT id FROM survey_sections WHERE survey_id = :survey_id AND title = :title"
            ),
            {"survey_id": survey_id, "title": title},
        ).scalar()
        if existing is None:
            order_by_survey[survey_id] = order_by_survey.get(survey_id, 0) + 1
            result = bind.execute(
                sa.text(
                    "INSERT INTO survey_sections "
                    "(survey_id, title, sort_order, created_at, updated_at) "
                    "VALUES (:survey_id, :title, :sort_order, :created_at, :updated_at)"
                ),
                {
                    "survey_id": survey_id,
                    "title": title,
                    "sort_order": order_by_survey[survey_id],
                    "created_at": now,
                    "updated_at": now,
                },
            )
            existing = result.lastrowid
        bind.execute(
            sa.text(
                "UPDATE survey_questions SET section_id = :section_id "
                "WHERE survey_id = :survey_id AND section = :title"
            ),
            {"section_id": existing, "survey_id": survey_id, "title": title},
        )


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("survey_questions")}
    with op.batch_alter_table("survey_questions") as batch:
        if "no_score" in columns:
            batch.drop_column("no_score")
        if "yes_score" in columns:
            batch.drop_column("yes_score")
        if "section_id" in columns:
            batch.drop_index("ix_survey_questions_section_id")
            batch.drop_constraint("fk_survey_questions_section_id", type_="foreignkey")
            batch.drop_column("section_id")
    if "survey_sections" in set(sa.inspect(bind).get_table_names()):
        op.drop_index("ix_survey_sections_order", table_name="survey_sections")
        op.drop_table("survey_sections")
