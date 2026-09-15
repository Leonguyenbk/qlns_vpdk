"""Tập hợp toàn bộ model để Alembic autogenerate và ứng dụng import."""
from __future__ import annotations

from .audit import AuditLog
from .employee import Employee, EmployeeAssignment, EmployeeEducation, JobGrade
from .kpi import (
    KpiCriteriaSet,
    KpiCriterion,
    KpiEvaluationComment,
    KpiPeriod,
    KpiScore,
    KpiScoreDetail,
    Product,
    ProductCatalogGroup,
    ProductConversion,
)
from .notification import Notification
from .organization import OrganizationUnit
from .position import Position, UnitPositionLimit
from .rbac import Permission, Role, UserUnitScope, role_permissions, user_roles
from .survey import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyResponse
from .task import (
    Task,
    TaskAssignment,
    TaskAttachment,
    TaskLog,
    TaskPause,
    TaskTemplate,
)
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
    "Notification",
    # Khảo sát
    "Survey",
    "SurveyQuestion",
    "SurveyOption",
    "SurveyResponse",
    "SurveyAnswer",
    # Giao việc
    "Task",
    "TaskAssignment",
    "TaskAttachment",
    "TaskLog",
    "TaskPause",
    "TaskTemplate",
    # KPI
    "ProductCatalogGroup",
    "Product",
    "ProductConversion",
    "KpiCriteriaSet",
    "KpiCriterion",
    "KpiPeriod",
    "KpiScore",
    "KpiScoreDetail",
    "KpiEvaluationComment",
]
