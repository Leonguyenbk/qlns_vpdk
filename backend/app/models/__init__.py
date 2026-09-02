"""Tập hợp toàn bộ model để Alembic autogenerate và ứng dụng import."""
from __future__ import annotations

from .audit import AuditLog
from .employee import Employee, EmployeeAssignment, EmployeeEducation, JobGrade
from .organization import OrganizationUnit
from .position import Position, UnitPositionLimit
from .rbac import Permission, Role, UserUnitScope, role_permissions, user_roles
from .token import RefreshToken
from .user import User

__all__ = [
    "AuditLog",
    "Employee",
    "EmployeeAssignment",
    "EmployeeEducation",
    "JobGrade",
    "OrganizationUnit",
    "Position",
    "UnitPositionLimit",
    "Permission",
    "Role",
    "UserUnitScope",
    "role_permissions",
    "user_roles",
    "RefreshToken",
    "User",
]
