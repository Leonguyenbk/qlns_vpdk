"""Lời chào + giới hạn số lượt khảo sát theo chi nhánh

Revision ID: 0015_survey_branch_limits
Revises: 0014_office_leader_survey
Create Date: 2026-09-15

- surveys.welcome_message (Text, NULL): lời chào hiển thị đầu trang công
  khai, trước khi chọn chi nhánh/nhập thông tin cá nhân.
- Bảng mới survey_branch_limits: chỉ tiêu số lượt tối đa cho một chi nhánh
  trong MỘT khảo sát cụ thể (ví dụ BMT 1000, Buôn Đôn 500) — khi đủ, trang
  công khai khoá không nhận thêm phản hồi gán cho chi nhánh đó.

Idempotent — chỉ thêm cột/bảng nếu chưa có. Không đụng dữ liệu hiện có.
"""
import sqlalchemy as sa
from alembic import op

revision = "0015_survey_branch_limits"
down_revision = "0014_office_leader_survey"
branch_labels = None
depends_on = None

MYSQL_ARGS = {"mysql_charset": "utf8mb4", "mysql_engine": "InnoDB"}


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    cols = {c["name"] for c in insp.get_columns("surveys")}
    if "welcome_message" not in cols:
        op.add_column("surveys", sa.Column("welcome_message", sa.Text(), nullable=True))

    if "survey_branch_limits" not in set(insp.get_table_names()):
        op.create_table(
            "survey_branch_limits",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("survey_id", sa.Integer(), nullable=False),
            sa.Column("branch_id", sa.Integer(), nullable=False),
            sa.Column("max_responses", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["branch_id"], ["organization_units.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("survey_id", "branch_id", name="uq_survey_branch_limit"),
            **MYSQL_ARGS,
        )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if "survey_branch_limits" in set(insp.get_table_names()):
        op.drop_table("survey_branch_limits")

    cols = {c["name"] for c in insp.get_columns("surveys")}
    if "welcome_message" in cols:
        op.drop_column("surveys", "welcome_message")
