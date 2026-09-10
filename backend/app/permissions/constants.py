"""Danh mục permission và vai trò mẫu của hệ thống (giai đoạn 1)."""
from __future__ import annotations

# --- Nhóm quyền nhân sự ---
EMPLOYEE_VIEW = "employee.view"
EMPLOYEE_VIEW_SENSITIVE = "employee.view_sensitive"
EMPLOYEE_CREATE = "employee.create"
EMPLOYEE_UPDATE = "employee.update"
EMPLOYEE_DELETE = "employee.delete"
EMPLOYEE_RESTORE = "employee.restore"
EMPLOYEE_TRANSFER = "employee.transfer"
EMPLOYEE_HISTORY_ADJUST = "employee.history_adjust"

# --- Nhóm quyền đơn vị ---
UNIT_VIEW = "unit.view"
UNIT_MANAGE = "unit.manage"

# --- Nhóm quyền chức vụ ---
POSITION_VIEW = "position.view"
POSITION_MANAGE = "position.manage"

# --- Nhóm quyền tài khoản / phân quyền ---
USER_VIEW = "user.view"
USER_MANAGE = "user.manage"
ROLE_VIEW = "role.view"
ROLE_MANAGE = "role.manage"

# --- Nhật ký ---
AUDIT_VIEW = "audit.view"


PERMISSION_DEFINITIONS: list[tuple[str, str]] = [
    (EMPLOYEE_VIEW, "Xem danh sách và hồ sơ nhân sự"),
    (EMPLOYEE_VIEW_SENSITIVE, "Xem thông tin nhạy cảm của nhân sự (CCCD...)"),
    (EMPLOYEE_CREATE, "Thêm mới nhân sự"),
    (EMPLOYEE_UPDATE, "Chỉnh sửa hồ sơ nhân sự"),
    (EMPLOYEE_DELETE, "Xóa (mềm) nhân sự"),
    (EMPLOYEE_RESTORE, "Khôi phục nhân sự đã xóa"),
    (EMPLOYEE_TRANSFER, "Chuyển nhân sự giữa các đơn vị"),
    (EMPLOYEE_HISTORY_ADJUST, "Điều chỉnh lịch sử công tác"),
    (UNIT_VIEW, "Xem cơ cấu đơn vị"),
    (UNIT_MANAGE, "Quản lý (thêm/sửa/ngừng) đơn vị"),
    (POSITION_VIEW, "Xem danh mục chức vụ"),
    (POSITION_MANAGE, "Quản lý chức vụ và giới hạn chức vụ"),
    (USER_VIEW, "Xem danh sách tài khoản"),
    (USER_MANAGE, "Quản lý tài khoản, gán vai trò và phạm vi đơn vị"),
    (ROLE_VIEW, "Xem vai trò và quyền"),
    (ROLE_MANAGE, "Quản lý vai trò và quyền"),
    (AUDIT_VIEW, "Xem nhật ký thao tác"),
]

ALL_PERMISSIONS = [code for code, _ in PERMISSION_DEFINITIONS]


# Vai trò mẫu -> danh sách permission
ROLE_SYSTEM_ADMIN = "SYSTEM_ADMIN"
ROLE_HR_ADMIN = "HR_ADMIN"
ROLE_UNIT_MANAGER = "UNIT_MANAGER"
ROLE_VIEWER = "VIEWER"

ROLE_DEFINITIONS: dict[str, dict] = {
    ROLE_SYSTEM_ADMIN: {
        "name": "Quản trị hệ thống",
        "description": "Toàn quyền hệ thống, quản lý tài khoản, vai trò, quyền và toàn bộ đơn vị.",
        "is_system": True,
        "permissions": ALL_PERMISSIONS,
    },
    ROLE_HR_ADMIN: {
        "name": "Quản trị nhân sự",
        "description": "Quản lý nhân sự, đơn vị và chức vụ trên toàn hệ thống.",
        "is_system": True,
        "permissions": [
            EMPLOYEE_VIEW,
            EMPLOYEE_VIEW_SENSITIVE,
            EMPLOYEE_CREATE,
            EMPLOYEE_UPDATE,
            EMPLOYEE_DELETE,
            EMPLOYEE_RESTORE,
            EMPLOYEE_TRANSFER,
            EMPLOYEE_HISTORY_ADJUST,
            UNIT_VIEW,
            UNIT_MANAGE,
            POSITION_VIEW,
            POSITION_MANAGE,
            AUDIT_VIEW,
        ],
    },
    ROLE_UNIT_MANAGER: {
        "name": "Quản lý đơn vị",
        "description": "Xem và quản lý nhân sự trong phạm vi đơn vị được phân công.",
        "is_system": True,
        "permissions": [
            EMPLOYEE_VIEW,
            EMPLOYEE_VIEW_SENSITIVE,
            EMPLOYEE_CREATE,
            EMPLOYEE_UPDATE,
            EMPLOYEE_TRANSFER,
            UNIT_VIEW,
            POSITION_VIEW,
        ],
    },
    ROLE_VIEWER: {
        "name": "Người xem",
        "description": "Chỉ xem danh sách và thông tin không nhạy cảm.",
        "is_system": True,
        "permissions": [
            EMPLOYEE_VIEW,
            UNIT_VIEW,
            POSITION_VIEW,
        ],
    },
}
