"""Tập giá trị hợp lệ cho các trường dạng enum (lưu bằng chuỗi để dễ migrate)."""
from __future__ import annotations

UNIT_TYPES = {"HEAD_OFFICE", "DEPARTMENT", "BRANCH", "SECTION"}

GENDERS = {"MALE", "FEMALE", "OTHER"}

EMPLOYMENT_TYPES = {"OFFICIAL", "CONTRACT", "PROBATION", "COLLABORATOR", "SECONDED"}

EMPLOYEE_STATUSES = {
    "WORKING",
    "ON_LEAVE",
    "RETIRED",
    "RESIGNED",
    "TRANSFERRED",
    "INACTIVE",
}

ASSIGNMENT_TYPES = {
    "RECRUITMENT",
    "APPOINTMENT",
    "TRANSFER",
    "SECONDMENT",
    "REASSIGNMENT",
}
