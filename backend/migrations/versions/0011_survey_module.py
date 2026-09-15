"""Module Khảo sát – Đánh giá mức độ hài lòng

Revision ID: 0011_survey_module
Revises: 0010_staff_role
Create Date: 2026-09-15

Tạo 5 bảng mới (surveys, survey_questions, survey_options, survey_responses,
survey_answers) và seed 8 permission `survey.*` mới, gán vào các vai trò mẫu
hiện có (SYSTEM_ADMIN, HR_ADMIN, UNIT_MANAGER, GOISO_ADMIN, GOISO_BRANCH_ADMIN,
OFFICE_LEADER, ORG_PERSONNEL, UNIT_HEAD) theo `app/permissions/constants.py`.
CHỈ TẠO THÊM — không sửa/xoá bảng hiện có, không đụng dữ liệu nhân sự/gọi
số/giao việc/KPI. Idempotent: kiểm tra tồn tại trước khi tạo (an toàn khi
chạy lại).
"""
from alembic import op
import sqlalchemy as sa

from app.permissions.constants import PERMISSION_DEFINITIONS, ROLE_DEFINITIONS

revision = "0011_survey_module"
down_revision = "0010_staff_role"
branch_labels = None
depends_on = None

MYSQL_ARGS = {"mysql_charset": "utf8mb4", "mysql_engine": "InnoDB"}

_NEW_PERMISSION_CODES = [
    "survey.view",
    "survey.create",
    "survey.update",
    "survey.delete",
    "survey.manage_questions",
    "survey.view_statistics",
    "survey.export",
    "survey.manage_all_branches",
]


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    if "surveys" not in existing:
        op.create_table(
            "surveys",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=160), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("slug", name="uq_surveys_slug"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_surveys_slug", "surveys", ["slug"])
        op.create_index("ix_surveys_status", "surveys", ["status"])

    if "survey_questions" not in existing:
        op.create_table(
            "survey_questions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("survey_id", sa.Integer(), nullable=False),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("question_type", sa.String(length=20), nullable=False),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_survey_questions_survey_id", "survey_questions", ["survey_id"])
        op.create_index(
            "ix_survey_questions_sort_order", "survey_questions", ["survey_id", "sort_order"]
        )

    if "survey_options" not in existing:
        op.create_table(
            "survey_options",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("option_text", sa.String(length=500), nullable=False),
            sa.Column("option_value", sa.String(length=100), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["question_id"], ["survey_questions.id"], ondelete="CASCADE"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_survey_options_question_id", "survey_options", ["question_id"])
        op.create_index(
            "ix_survey_options_sort_order", "survey_options", ["question_id", "sort_order"]
        )

    if "survey_responses" not in existing:
        op.create_table(
            "survey_responses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("survey_id", sa.Integer(), nullable=False),
            sa.Column("branch_id", sa.Integer(), nullable=True),
            sa.Column("service_id", sa.Integer(), nullable=True),
            sa.Column("counter_id", sa.Integer(), nullable=True),
            sa.Column("employee_id", sa.Integer(), nullable=True),
            sa.Column("respondent_name", sa.String(length=255), nullable=True),
            sa.Column("respondent_phone", sa.String(length=20), nullable=True),
            sa.Column("ip_address", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("client_token", sa.String(length=64), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["branch_id"], ["organization_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="SET NULL"),
            sa.UniqueConstraint(
                "survey_id", "client_token", name="uq_survey_response_client_token"
            ),
            **MYSQL_ARGS,
        )
        op.create_index("ix_survey_responses_survey_id", "survey_responses", ["survey_id"])
        op.create_index("ix_survey_responses_submitted_at", "survey_responses", ["submitted_at"])
        op.create_index("ix_survey_responses_branch_id", "survey_responses", ["branch_id"])
        op.create_index("ix_survey_responses_service_id", "survey_responses", ["service_id"])
        op.create_index("ix_survey_responses_employee_id", "survey_responses", ["employee_id"])

    if "survey_answers" not in existing:
        op.create_table(
            "survey_answers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("response_id", sa.Integer(), nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("option_id", sa.Integer(), nullable=True),
            sa.Column("answer_text", sa.Text(), nullable=True),
            sa.Column("answer_number", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["response_id"], ["survey_responses.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["question_id"], ["survey_questions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["option_id"], ["survey_options.id"], ondelete="SET NULL"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_survey_answers_response_id", "survey_answers", ["response_id"])
        op.create_index("ix_survey_answers_question_id", "survey_answers", ["question_id"])
        op.create_index("ix_survey_answers_option_id", "survey_answers", ["option_id"])

    # --- Seed permission mới + gán vào vai trò mẫu hiện có (idempotent) ---
    # Lưu ý: migration 0002 đọc PERMISSION_DEFINITIONS/ROLE_DEFINITIONS "sống" từ
    # constants.py tại thời điểm chạy — khi migrate lại từ đầu (vd. test suite),
    # nó sẽ tự seed luôn các permission survey.* mới thêm ở đây, nên bước này
    # phải kiểm tra tồn tại trước khi chèn để không trùng khi nâng cấp từ đầu.
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    perm_desc = dict(PERMISSION_DEFINITIONS)
    existing_codes = {
        row.code
        for row in bind.execute(
            sa.select(permissions.c.code).where(permissions.c.code.in_(_NEW_PERMISSION_CODES))
        )
    }
    to_insert = [
        {"code": code, "description": perm_desc[code]}
        for code in _NEW_PERMISSION_CODES
        if code not in existing_codes
    ]
    if to_insert:
        op.bulk_insert(permissions, to_insert)

    perm_id = {
        row.code: row.id
        for row in bind.execute(
            sa.select(permissions.c.id, permissions.c.code).where(
                permissions.c.code.in_(_NEW_PERMISSION_CODES)
            )
        )
    }
    role_id = {row.code: row.id for row in bind.execute(sa.select(roles.c.id, roles.c.code))}
    existing_links = {
        (row.role_id, row.permission_id)
        for row in bind.execute(
            sa.select(role_permissions.c.role_id, role_permissions.c.permission_id).where(
                role_permissions.c.permission_id.in_(perm_id.values())
            )
        )
    }

    links = []
    for role_code, cfg in ROLE_DEFINITIONS.items():
        if role_code not in role_id:
            continue
        for pcode in cfg["permissions"]:
            if pcode not in perm_id:
                continue
            pair = (role_id[role_code], perm_id[pcode])
            if pair not in existing_links:
                links.append({"role_id": pair[0], "permission_id": pair[1]})
    if links:
        op.bulk_insert(role_permissions, links)


def downgrade():
    bind = op.get_bind()
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    perm_ids = [
        row.id
        for row in bind.execute(
            sa.select(permissions.c.id).where(permissions.c.code.in_(_NEW_PERMISSION_CODES))
        )
    ]
    if perm_ids:
        bind.execute(role_permissions.delete().where(role_permissions.c.permission_id.in_(perm_ids)))
        bind.execute(permissions.delete().where(permissions.c.id.in_(perm_ids)))

    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())
    for table in ("survey_answers", "survey_responses", "survey_options", "survey_questions", "surveys"):
        if table in existing:
            op.drop_table(table)
