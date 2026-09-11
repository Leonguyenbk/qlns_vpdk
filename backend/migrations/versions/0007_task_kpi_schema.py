"""Phân hệ Giao việc – Theo dõi nhiệm vụ – Đánh giá KPI

Revision ID: 0007_task_kpi_schema
Revises: 0006_goiso_tables
Create Date: 2026-09-11

Bổ sung bảng mới (giao việc, danh mục sản phẩm, KPI, thông báo). Migration
CHỈ TẠO THÊM — không sửa/xoá bảng hiện có, không đụng dữ liệu nhân sự/gọi số.
Idempotent: kiểm tra tồn tại trước khi tạo (an toàn khi chạy lại).

Xem docs/TASK_KPI_ANALYSIS.md để biết đối chiếu nghiệp vụ và các điểm còn
chờ cấp có thẩm quyền xác nhận.
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0007_task_kpi_schema"
down_revision = "0006_goiso_tables"
branch_labels = None
depends_on = None

MYSQL_ARGS = {"mysql_charset": "utf8mb4", "mysql_engine": "InnoDB"}

# 18 nhóm sản phẩm/công việc — trích trực tiếp Phụ lục II của tài liệu dự
# thảo (mục 24). Đây là dữ liệu tham chiếu của chính tài liệu, KHÔNG phải dữ
# liệu demo — nhưng tên/mô tả vẫn ở trạng thái dự thảo, có thể chỉnh trong
# Admin KPI khi ban hành Quy chế chính thức.
_CATALOG_GROUPS = [
    ("N1", "Tiếp nhận và trả kết quả thủ tục hành chính",
     "Thấp – Trung bình (tùy loại TTHC)",
     "Trung bình – Cao: ảnh hưởng trực tiếp uy tín, mức độ hài lòng của người dân, "
     "doanh nghiệp; là nguồn phát sinh khiếu nại, phản ánh phổ biến nhất."),
    ("N2", "Đăng ký đất đai và cấp Giấy chứng nhận (lần đầu)",
     "Trung bình – Cao (tùy nguồn gốc, tình trạng pháp lý thửa đất)",
     "Cao – Rất cao: có thể dẫn đến thu hồi, hủy Giấy chứng nhận, tranh chấp, "
     "khiếu kiện kéo dài, trách nhiệm bồi thường."),
    ("N3", "Đăng ký biến động đất đai",
     "Trung bình – Cao (tùy loại biến động)",
     "Cao: sai lệch giữa hồ sơ giấy và CSDL dẫn đến tranh chấp giao dịch, ảnh "
     "hưởng quyền của bên thứ ba."),
    ("N4", "Cấp đổi, cấp lại và đính chính Giấy chứng nhận",
     "Trung bình",
     "Trung bình – Cao: sai sót lặp lại làm phát sinh khiếu nại nhiều lần."),
    ("N5", "Đo đạc, trích đo địa chính",
     "Cao (yêu cầu kỹ thuật trắc địa chuyên sâu)",
     "Cao – Rất cao: là nguyên nhân gốc dẫn đến sai lệch toàn bộ hồ sơ, Giấy "
     "chứng nhận, tranh chấp ranh giới về sau."),
    ("N6", "Lập, kiểm tra và chỉnh lý bản đồ địa chính",
     "Cao",
     "Cao: ảnh hưởng đến toàn bộ dữ liệu không gian địa chính."),
    ("N7", "Xây dựng, cập nhật và chỉnh lý hồ sơ địa chính",
     "Trung bình",
     "Trung bình – Cao: gây khó khăn cho tra cứu, xác minh nguồn gốc đất."),
    ("N8", "Xây dựng, cập nhật và kiểm tra cơ sở dữ liệu địa chính",
     "Trung bình – Cao",
     "Cao – Rất cao: sai lệch CSDL ảnh hưởng toàn bộ hoạt động tra cứu, liên "
     "thông dữ liệu với các ngành khác."),
    ("N9", "Quét, số hóa và liên kết hồ sơ",
     "Thấp – Trung bình",
     "Trung bình: có thể khắc phục bằng đối chiếu hồ sơ gốc."),
    ("N10", "Cung cấp dữ liệu và thông tin đất đai",
     "Thấp – Trung bình",
     "Cao: thông tin sai có thể ảnh hưởng giao dịch dân sự, phát sinh trách "
     "nhiệm bồi thường."),
    ("N11", "Luân chuyển thông tin xác định nghĩa vụ tài chính",
     "Trung bình",
     "Cao: ảnh hưởng trực tiếp quyền lợi tài chính và nguồn thu ngân sách."),
    ("N12", "Thu, quản lý phí và lệ phí",
     "Trung bình",
     "Cao: liên quan trách nhiệm quản lý tài chính công."),
    ("N13", "Tiếp nhận, phân loại và tham mưu giải quyết đơn thư",
     "Trung bình – Cao",
     "Cao: ảnh hưởng quyền khiếu nại, tố cáo của công dân."),
    ("N14", "Kiểm tra, thanh tra và xử lý sai sót nghiệp vụ",
     "Trung bình – Cao",
     "Cao: là tuyến kiểm soát cuối cùng phát hiện sai sót nghiệp vụ."),
    ("N15", "Hành chính, tổng hợp, tổ chức cán bộ và kế toán",
     "Thấp – Trung bình",
     "Thấp – Trung bình: chủ yếu ảnh hưởng nội bộ."),
    ("N16", "Quản lý, chỉ đạo, điều hành và kiểm tra",
     "Cao",
     "Cao: ảnh hưởng kết quả chung của cả đơn vị/Chi nhánh."),
    ("N17", "Thực hiện đề án, kế hoạch và nhiệm vụ chuyên đề",
     "Cao",
     "Trung bình – Cao: tùy quy mô, tầm quan trọng của đề án."),
    ("N18", "Thực hiện nhiệm vụ đột xuất",
     "Tùy tính chất nhiệm vụ cụ thể, xác định tại thời điểm giao việc",
     "Trung bình – Cao: tùy mức độ khẩn cấp, quan trọng."),
]


def _now():
    return datetime.now(timezone.utc)


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    if "product_catalog_groups" not in existing:
        op.create_table(
            "product_catalog_groups",
            sa.Column("code", sa.String(length=10), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("complexity_note", sa.Text(), nullable=True),
            sa.Column("error_impact_note", sa.Text(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            **MYSQL_ARGS,
        )
        op.bulk_insert(
            sa.table(
                "product_catalog_groups",
                sa.column("code", sa.String),
                sa.column("name", sa.String),
                sa.column("complexity_note", sa.Text),
                sa.column("error_impact_note", sa.Text),
                sa.column("sort_order", sa.Integer),
            ),
            [
                {
                    "code": code,
                    "name": name,
                    "complexity_note": complexity,
                    "error_impact_note": impact,
                    "sort_order": i,
                }
                for i, (code, name, complexity, impact) in enumerate(_CATALOG_GROUPS, start=1)
            ],
        )

    if "products" not in existing:
        op.create_table(
            "products",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("group_code", sa.String(length=10), nullable=False),
            sa.Column("code", sa.String(length=30), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("unit_of_measure", sa.String(length=50), nullable=True),
            sa.Column("is_standard_product", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("status", sa.String(length=10), nullable=False, server_default="DRAFT"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("effective_date", sa.Date(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["group_code"], ["product_catalog_groups.code"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("code", name="uq_products_code"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_products_group_code", "products", ["group_code"])
        op.create_index("ix_products_code", "products", ["code"])

    if "product_conversions" not in existing:
        op.create_table(
            "product_conversions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("kn_value", sa.Numeric(6, 3), nullable=True),
            sa.Column("cap_value", sa.Numeric(14, 2), nullable=True),
            sa.Column("standard_time_hours", sa.Numeric(10, 2), nullable=True),
            sa.Column("effective_from", sa.Date(), nullable=False),
            sa.Column("effective_to", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=10), nullable=False, server_default="DRAFT"),
            sa.Column("approved_by", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_product_conversions_product", "product_conversions", ["product_id"])

    if "tasks" not in existing:
        op.create_table(
            "tasks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=500), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("business_group_code", sa.String(length=10), nullable=True),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("source", sa.String(length=20), nullable=False, server_default="AD_HOC"),
            sa.Column("creator_id", sa.Integer(), nullable=False),
            sa.Column("assigner_id", sa.Integer(), nullable=False),
            sa.Column("assigning_unit_id", sa.Integer(), nullable=False),
            sa.Column("executing_unit_id", sa.Integer(), nullable=True),
            sa.Column("parent_task_id", sa.Integer(), nullable=True),
            sa.Column("has_own_product", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("priority", sa.String(length=10), nullable=False, server_default="NORMAL"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
            sa.Column("assigned_date", sa.Date(), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("original_deadline", sa.Date(), nullable=True),
            sa.Column("extended_deadline", sa.Date(), nullable=True),
            sa.Column("deadline_type", sa.String(length=10), nullable=False, server_default="INTERNAL"),
            sa.Column("assigned_workload", sa.Numeric(14, 2), nullable=True),
            sa.Column("workload_unit", sa.String(length=50), nullable=True),
            sa.Column("output_description", sa.Text(), nullable=True),
            sa.Column("quality_standard", sa.Text(), nullable=True),
            sa.Column("acceptance_conditions", sa.Text(), nullable=True),
            sa.Column("complexity_level", sa.String(length=30), nullable=True),
            sa.Column("kn_snapshot", sa.Numeric(6, 3), nullable=True),
            sa.Column("cap_snapshot", sa.Numeric(14, 2), nullable=True),
            sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("result_summary", sa.Text(), nullable=True),
            sa.Column("quality_level", sa.Integer(), nullable=True),
            sa.Column("error_severity", sa.String(length=30), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("accepted_by", sa.Integer(), nullable=True),
            sa.Column("rework_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("blocker_reason", sa.Text(), nullable=True),
            sa.Column("cancel_reason", sa.Text(), nullable=True),
            sa.Column("cancelled_by", sa.Integer(), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["business_group_code"], ["product_catalog_groups.code"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["assigner_id"], ["users.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["assigning_unit_id"], ["organization_units.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["executing_unit_id"], ["organization_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["parent_task_id"], ["tasks.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["accepted_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["cancelled_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
            sa.UniqueConstraint("code", name="uq_tasks_code"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_tasks_code", "tasks", ["code"])
        op.create_index("ix_tasks_status", "tasks", ["status"])
        op.create_index("ix_tasks_assigning_unit", "tasks", ["assigning_unit_id"])
        op.create_index("ix_tasks_executing_unit", "tasks", ["executing_unit_id"])
        op.create_index("ix_tasks_parent", "tasks", ["parent_task_id"])
        op.create_index("ix_tasks_deadline", "tasks", ["extended_deadline", "original_deadline"])
        op.create_index("ix_tasks_business_group_code", "tasks", ["business_group_code"])
        op.create_index("ix_tasks_product_id", "tasks", ["product_id"])

    if "task_assignments" not in existing:
        op.create_table(
            "task_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role_in_task", sa.String(length=15), nullable=False, server_default="LEAD"),
            sa.Column("contribution_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("unit_id_snapshot", sa.Integer(), nullable=True),
            sa.Column("position_id_snapshot", sa.Integer(), nullable=True),
            sa.Column("position_name_snapshot", sa.String(length=150), nullable=True),
            sa.Column("is_managerial_snapshot", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("assigned_by", sa.Integer(), nullable=True),
            sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("removed_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["unit_id_snapshot"], ["organization_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["position_id_snapshot"], ["positions.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_task_assignments_task", "task_assignments", ["task_id"])
        op.create_index("ix_task_assignments_user", "task_assignments", ["user_id"])

    if "task_pauses" not in existing:
        op.create_table(
            "task_pauses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("reason_code", sa.String(length=30), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("evidence_ref", sa.String(length=255), nullable=True),
            sa.Column("confirmed_by", sa.Integer(), nullable=True),
            sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_task_pauses_task", "task_pauses", ["task_id"])

    if "task_logs" not in existing:
        op.create_table(
            "task_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("log_kind", sa.String(length=30), nullable=False),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_task_logs_task", "task_logs", ["task_id"])
        op.create_index("ix_task_logs_created_at", "task_logs", ["created_at"])

    if "task_attachments" not in existing:
        op.create_table(
            "task_attachments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("task_log_id", sa.Integer(), nullable=True),
            sa.Column("uploaded_by", sa.Integer(), nullable=False),
            sa.Column("kind", sa.String(length=15), nullable=False, server_default="EVIDENCE"),
            sa.Column("file_name", sa.String(length=255), nullable=False),
            sa.Column("stored_path", sa.String(length=500), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("content_type", sa.String(length=150), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["task_log_id"], ["task_logs.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_task_attachments_task", "task_attachments", ["task_id"])

    if "task_templates" not in existing:
        op.create_table(
            "task_templates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("business_group_code", sa.String(length=10), nullable=True),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("default_output_description", sa.Text(), nullable=True),
            sa.Column("default_quality_standard", sa.Text(), nullable=True),
            sa.Column("default_acceptance_conditions", sa.Text(), nullable=True),
            sa.Column("default_workload", sa.Numeric(14, 2), nullable=True),
            sa.Column("default_workload_unit", sa.String(length=50), nullable=True),
            sa.Column("default_priority", sa.String(length=10), nullable=False, server_default="NORMAL"),
            sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("recurrence_interval", sa.String(length=10), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["business_group_code"], ["product_catalog_groups.code"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
            **MYSQL_ARGS,
        )

    if "kpi_criteria_sets" not in existing:
        op.create_table(
            "kpi_criteria_sets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(length=10), nullable=False, server_default="DRAFT"),
            sa.Column("scope_unit_id", sa.Integer(), nullable=True),
            sa.Column("applicable_position_type", sa.String(length=15), nullable=False, server_default="ALL"),
            sa.Column("applies_to_contract_labor", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("effective_from", sa.Date(), nullable=False),
            sa.Column("effective_to", sa.Date(), nullable=True),
            sa.Column("approved_by", sa.Integer(), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reference_documents", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["scope_unit_id"], ["organization_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
            **MYSQL_ARGS,
        )

    if "kpi_criteria" not in existing:
        op.create_table(
            "kpi_criteria",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("criteria_set_id", sa.Integer(), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("code", sa.String(length=30), nullable=False),
            sa.Column("name", sa.String(length=500), nullable=False),
            sa.Column("kind", sa.String(length=30), nullable=False),
            sa.Column("max_points", sa.Numeric(5, 2), nullable=False, server_default="0"),
            sa.Column("formula_key", sa.String(length=30), nullable=True),
            sa.Column("requires_evidence", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("needs_confirmation", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["criteria_set_id"], ["kpi_criteria_sets.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["parent_id"], ["kpi_criteria.id"], ondelete="CASCADE"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_kpi_criteria_set", "kpi_criteria", ["criteria_set_id"])

    if "kpi_periods" not in existing:
        op.create_table(
            "kpi_periods",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=20), nullable=False),
            sa.Column("period_type", sa.String(length=10), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(length=10), nullable=False, server_default="OPEN"),
            sa.Column("criteria_set_id", sa.Integer(), nullable=True),
            sa.Column("explanation_deadline_days", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("locked_by", sa.Integer(), nullable=True),
            sa.Column("reopened_reason", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["criteria_set_id"], ["kpi_criteria_sets.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["locked_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
            sa.UniqueConstraint("code", name="uq_kpi_periods_code"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_kpi_periods_code", "kpi_periods", ["code"])

    if "kpi_scores" not in existing:
        op.create_table(
            "kpi_scores",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("period_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("employee_id_snapshot", sa.Integer(), nullable=True),
            sa.Column("unit_id_snapshot", sa.Integer(), nullable=True),
            sa.Column("position_id_snapshot", sa.Integer(), nullable=True),
            sa.Column("position_name_snapshot", sa.String(length=150), nullable=True),
            sa.Column("is_managerial_snapshot", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("criteria_set_id_snapshot", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=15), nullable=False, server_default="DRAFT"),
            sa.Column("provisional_total", sa.Numeric(6, 2), nullable=True),
            sa.Column("self_assessed_total", sa.Numeric(6, 2), nullable=True),
            sa.Column("confirmed_total", sa.Numeric(6, 2), nullable=True),
            sa.Column("proposed_rating", sa.String(length=50), nullable=True),
            sa.Column("official_rating", sa.String(length=50), nullable=True),
            sa.Column("self_assessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("aggregated_by", sa.Integer(), nullable=True),
            sa.Column("aggregated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by", sa.Integer(), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("replaces_id", sa.Integer(), nullable=True),
            sa.Column("replace_reason", sa.Text(), nullable=True),
            sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["period_id"], ["kpi_periods.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["employee_id_snapshot"], ["employees.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["unit_id_snapshot"], ["organization_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["position_id_snapshot"], ["positions.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["criteria_set_id_snapshot"], ["kpi_criteria_sets.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["aggregated_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["replaces_id"], ["kpi_scores.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
            sa.UniqueConstraint("period_id", "user_id", "replaces_id", name="uq_kpi_scores_period_user_version"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_kpi_scores_period", "kpi_scores", ["period_id"])
        op.create_index("ix_kpi_scores_user", "kpi_scores", ["user_id"])

    if "kpi_score_details" not in existing:
        op.create_table(
            "kpi_score_details",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kpi_score_id", sa.Integer(), nullable=False),
            sa.Column("criteria_id", sa.Integer(), nullable=False),
            sa.Column("raw_numerator", sa.Numeric(14, 2), nullable=True),
            sa.Column("raw_denominator", sa.Numeric(14, 2), nullable=True),
            sa.Column("ratio_percent", sa.Numeric(6, 2), nullable=True),
            sa.Column("points_earned", sa.Numeric(6, 2), nullable=True),
            sa.Column("max_points", sa.Numeric(5, 2), nullable=False, server_default="0"),
            sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("evaluator_id", sa.Integer(), nullable=True),
            sa.Column("evaluator_comment", sa.Text(), nullable=True),
            sa.Column("evidence_refs", sa.JSON(), nullable=True),
            sa.Column("needs_confirmation", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["kpi_score_id"], ["kpi_scores.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["criteria_id"], ["kpi_criteria.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["evaluator_id"], ["users.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("kpi_score_id", "criteria_id", name="uq_kpi_score_detail"),
            **MYSQL_ARGS,
        )

    if "kpi_evaluation_comments" not in existing:
        op.create_table(
            "kpi_evaluation_comments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kpi_score_id", sa.Integer(), nullable=False),
            sa.Column("comment_type", sa.String(length=30), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=True),
            sa.Column("author_role_label", sa.String(length=150), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=15), nullable=False, server_default="OPEN"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["kpi_score_id"], ["kpi_scores.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_kpi_eval_comments_score", "kpi_evaluation_comments", ["kpi_score_id"])

    if "notifications" not in existing:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("type", sa.String(length=30), nullable=False),
            sa.Column("entity_type", sa.String(length=30), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("dedupe_day", sa.String(length=10), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint(
                "user_id", "type", "entity_type", "entity_id", "dedupe_day",
                name="uq_notification_dedupe",
            ),
            **MYSQL_ARGS,
        )
        op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "is_read"])


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())
    # Thứ tự xoá ngược phụ thuộc khoá ngoại
    for table in (
        "notifications",
        "kpi_evaluation_comments",
        "kpi_score_details",
        "kpi_scores",
        "kpi_periods",
        "kpi_criteria",
        "kpi_criteria_sets",
        "task_templates",
        "task_attachments",
        "task_logs",
        "task_pauses",
        "task_assignments",
        "tasks",
        "product_conversions",
        "products",
        "product_catalog_groups",
    ):
        if table in existing:
            op.drop_table(table)
