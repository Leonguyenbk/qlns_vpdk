"""Bảng dữ liệu module Gọi số (goiso_*) trong CSDL chung + liên kết đơn vị

Revision ID: 0006_goiso_tables
Revises: 0005_goiso_permissions_roles
Create Date: 2026-09-10

Phase 6: đưa kho dữ liệu goiso vào cùng CSDL với nhân sự, tiền tố goiso_.
Dữ liệu được nạp từ SQLite (hethong_v2.db) bằng scripts/migrate_goiso.py.
"""
import sqlalchemy as sa
from alembic import op

revision = "0006_goiso_tables"
down_revision = "0005_goiso_permissions_roles"
branch_labels = None
depends_on = None

_TABLES = [
    "goiso_branches",
    "goiso_queue",
    "goiso_counters_status",
    "goiso_config",
    "goiso_visitor_stats",
    "goiso_appointments",
    "goiso_devices",
]


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    if "goiso_branches" not in existing:
        op.create_table(
            "goiso_branches",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("code", sa.String(50), nullable=False, unique=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("full_name", sa.String(255), nullable=False),
            sa.Column("address", sa.String(255), server_default=""),
            sa.Column("active", sa.Integer, server_default="1"),
            sa.Column("display_order", sa.Integer, server_default="99"),
            sa.Column("api_key", sa.String(64), nullable=False),
            sa.Column("display_token", sa.String(64), nullable=False),
            sa.Column("created_at", sa.String(30)),
        )

    if "goiso_queue" not in existing:
        op.create_table(
            "goiso_queue",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("branch_id", sa.Integer, nullable=False),
            sa.Column("prefix", sa.String(16)),
            sa.Column("number", sa.Integer),
            sa.Column("status", sa.String(16)),
            sa.Column("counter", sa.String(64), server_default=""),
            sa.Column("staff_name", sa.String(255), server_default=""),
            sa.Column("date_record", sa.String(10)),
            sa.Column("time_issue", sa.String(30)),
            sa.Column("time_start", sa.String(30)),
            sa.Column("time_done", sa.String(30)),
            sa.Column("fullname", sa.String(255), server_default=""),
            sa.Column("cccd", sa.String(20), server_default=""),
            sa.Column("phone", sa.String(20), server_default=""),
            sa.Column("session", sa.String(10), server_default=""),
            sa.Column("source", sa.String(16), server_default="kiosk"),
            sa.Column("priority", sa.Integer, server_default="0"),
            sa.Column("appointment_id", sa.Integer),
        )
        op.create_index(
            "idx_goiso_queue_main",
            "goiso_queue",
            ["branch_id", "date_record", "prefix", "status", "number"],
        )
        op.create_index(
            "idx_goiso_queue_counter",
            "goiso_queue",
            ["branch_id", "date_record", "counter", "status"],
        )

    if "goiso_counters_status" not in existing:
        op.create_table(
            "goiso_counters_status",
            sa.Column("branch_id", sa.Integer, nullable=False),
            sa.Column("counter_id", sa.String(64), nullable=False),
            sa.Column("staff_name", sa.String(255), server_default=""),
            sa.Column("status", sa.String(16), server_default="offline"),
            sa.Column("last_num", sa.String(16), server_default=""),
            sa.Column("last_update", sa.String(30)),
            sa.PrimaryKeyConstraint("branch_id", "counter_id"),
        )

    if "goiso_config" not in existing:
        op.create_table(
            "goiso_config",
            sa.Column("branch_id", sa.Integer, nullable=False, server_default="0"),
            sa.Column("key", sa.String(64), nullable=False),
            sa.Column("value", sa.Text),
            sa.PrimaryKeyConstraint("branch_id", "key"),
        )

    if "goiso_visitor_stats" not in existing:
        op.create_table(
            "goiso_visitor_stats",
            sa.Column("branch_id", sa.Integer, nullable=False),
            sa.Column("date_record", sa.String(10), nullable=False),
            sa.Column("count", sa.Integer, server_default="0"),
            sa.PrimaryKeyConstraint("branch_id", "date_record"),
        )

    if "goiso_appointments" not in existing:
        op.create_table(
            "goiso_appointments",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("branch_id", sa.Integer, nullable=False),
            sa.Column("prefix", sa.String(16), nullable=False),
            sa.Column("slot_date", sa.String(10), nullable=False),
            sa.Column("slot_start", sa.String(5), nullable=False),
            sa.Column("slot_end", sa.String(5), nullable=False),
            sa.Column("code", sa.String(16), nullable=False),
            sa.Column("token", sa.String(64), nullable=False, unique=True),
            sa.Column("citizen_name", sa.String(255), server_default=""),
            sa.Column("cccd", sa.String(20), server_default=""),
            sa.Column("phone", sa.String(20), server_default=""),
            sa.Column("status", sa.String(16), server_default="booked"),
            sa.Column("created_at", sa.String(30)),
            sa.Column("checkin_at", sa.String(30)),
            sa.Column("queue_id", sa.Integer),
            sa.Column("ip", sa.String(64), server_default=""),
        )
        op.create_index(
            "idx_goiso_appt_slot",
            "goiso_appointments",
            ["branch_id", "slot_date", "prefix", "status"],
        )
        op.create_index(
            "idx_goiso_appt_code", "goiso_appointments", ["branch_id", "code"]
        )
        op.create_index(
            "idx_goiso_appt_cccd", "goiso_appointments", ["branch_id", "cccd", "status"]
        )

    if "goiso_devices" not in existing:
        op.create_table(
            "goiso_devices",
            sa.Column("device_id", sa.String(128), primary_key=True),
            sa.Column("branch_code", sa.String(50), server_default=""),
            sa.Column("name", sa.String(255), server_default=""),
            sa.Column("version", sa.String(30), server_default=""),
            sa.Column("printer", sa.String(255), server_default=""),
            sa.Column("paper_mm", sa.Integer, server_default="80"),
            sa.Column("status", sa.String(16), server_default="online"),
            sa.Column("update_status", sa.String(64), server_default=""),
            sa.Column("first_seen", sa.String(30)),
            sa.Column("last_seen", sa.String(30)),
            sa.Column("extra", sa.Text),
        )

    # Liên kết đơn vị dùng chung <-> chi nhánh goiso
    ou_cols = {c["name"] for c in insp.get_columns("organization_units")}
    if "goiso_branch_code" not in ou_cols:
        op.add_column(
            "organization_units",
            sa.Column("goiso_branch_code", sa.String(50), nullable=True),
        )
        idx = {i["name"] for i in insp.get_indexes("organization_units")}
        if "ix_organization_units_goiso_branch_code" not in idx:
            op.create_index(
                "ix_organization_units_goiso_branch_code",
                "organization_units",
                ["goiso_branch_code"],
            )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "goiso_branch_code" in {
        c["name"] for c in insp.get_columns("organization_units")
    }:
        if "ix_organization_units_goiso_branch_code" in {
            i["name"] for i in insp.get_indexes("organization_units")
        }:
            op.drop_index(
                "ix_organization_units_goiso_branch_code",
                table_name="organization_units",
            )
        op.drop_column("organization_units", "goiso_branch_code")
    existing = set(insp.get_table_names())
    for t in reversed(_TABLES):
        if t in existing:
            op.drop_table(t)
