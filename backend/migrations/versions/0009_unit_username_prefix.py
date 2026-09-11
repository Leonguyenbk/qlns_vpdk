"""Tiền tố username theo Phòng/Chi nhánh — phục vụ tạo tài khoản hàng loạt và
tự đổi tiền tố username khi nhân sự chuyển đơn vị.

Revision ID: 0009_unit_username_prefix
Revises: 0008_task_kpi_permissions
Create Date: 2026-09-11

- Thêm cột organization_units.username_prefix (VARCHAR(20), UNIQUE, NULL).
- Backfill cho 24 Chi nhánh: lấy đúng goiso_branch_code hiện có (để tài khoản
  mới tạo cùng tiền tố với tài khoản gọi số cũ, ví dụ 'bmt').
- Backfill cho 5 đơn vị cấp Phòng/Ban tại Văn phòng (không có goiso_branch_code
  vì không phải chi nhánh) — đặt tiền tố tường minh, có thể sửa sau qua Admin.

Idempotent — chỉ set giá trị còn NULL, không ghi đè tiền tố đã có.
"""
import sqlalchemy as sa
from alembic import op

revision = "0009_unit_username_prefix"
down_revision = "0008_task_kpi_permissions"
branch_labels = None
depends_on = None

# Mã đơn vị (organization_units.code, ổn định) -> tiền tố username đề xuất.
# Chỉ áp dụng cho 5 đơn vị cấp Phòng/Ban tại Văn phòng tỉnh (không phải Chi
# nhánh) — Giám đốc VPĐKĐĐ có thể đổi lại qua Admin nếu muốn tên khác.
_DEPARTMENT_PREFIXES = {
    "van-phong-dang-ky-tinh.ban-giam-doc": "vpbgd",
    "van-phong-dang-ky-tinh.phong-to-chuc-hanh-chinh": "tchc",
    "van-phong-dang-ky-tinh.phong-ke-hoach-tai-chinh": "khtc",
    "van-phong-dang-ky-tinh.phong-ky-thuat-dang-ky-dat-": "kt",
    "van-phong-dang-ky-tinh.phong-du-lieu-thong-tin-dat": "dl",
}


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("organization_units")}
    if "username_prefix" not in cols:
        op.add_column("organization_units", sa.Column("username_prefix", sa.String(length=20), nullable=True))
        op.create_index("ix_organization_units_username_prefix", "organization_units", ["username_prefix"])

    meta = sa.MetaData()
    units = sa.Table("organization_units", meta, autoload_with=bind)

    # Chi nhánh: lấy theo goiso_branch_code hiện có
    bind.execute(
        sa.text(
            "UPDATE organization_units SET username_prefix = goiso_branch_code "
            "WHERE username_prefix IS NULL AND goiso_branch_code IS NOT NULL "
            "AND unit_type = 'BRANCH'"
        )
    )

    # Phòng/Ban tại Văn phòng tỉnh: đặt tường minh theo mã đơn vị
    for code, prefix in _DEPARTMENT_PREFIXES.items():
        bind.execute(
            sa.text(
                "UPDATE organization_units SET username_prefix = :p "
                "WHERE code = :c AND username_prefix IS NULL"
            ),
            {"p": prefix, "c": code},
        )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("organization_units")}
    if "username_prefix" in cols:
        indexes = {i["name"] for i in insp.get_indexes("organization_units")}
        if "ix_organization_units_username_prefix" in indexes:
            op.drop_index("ix_organization_units_username_prefix", table_name="organization_units")
        op.drop_column("organization_units", "username_prefix")
