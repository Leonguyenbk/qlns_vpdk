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

# --- Phân hệ Giao việc – Theo dõi nhiệm vụ – Đánh giá KPI ---

TASK_SOURCES = {"PLAN", "DIRECTIVE", "ROUTINE", "CASE_FILE", "AD_HOC"}

TASK_PRIORITIES = {"LOW", "NORMAL", "HIGH", "URGENT"}

# "Quá hạn" KHÔNG nằm trong tập này — đó là chỉ số tính toán (is_overdue),
# không phải trạng thái được lưu (theo đúng yêu cầu nghiệp vụ).
TASK_STATUSES = {
    "DRAFT",              # Nháp
    "ASSIGNED",           # Đã giao
    "IN_PROGRESS",        # Đang thực hiện
    "PENDING_COLLAB",     # Chờ phối hợp
    "PAUSED",             # Tạm dừng
    "NEEDS_REVISION",     # Yêu cầu bổ sung/làm lại
    "PENDING_ACCEPTANCE", # Chờ nghiệm thu
    "COMPLETED",          # Hoàn thành (chỉ người có thẩm quyền nghiệm thu mới đặt được)
    "CANCELLED",          # Đã hủy
}

TASK_TERMINAL_STATUSES = {"COMPLETED", "CANCELLED"}

TASK_DEADLINE_TYPES = {"INTERNAL", "TTHC"}

TASK_ASSIGNMENT_ROLES = {"LEAD", "COLLABORATOR", "REVIEWER"}

TASK_LOG_KINDS = {
    "COMMENT",
    "WORK_LOG",
    "STATUS_CHANGE",
    "SUBMISSION",
    "RETURN_FOR_REVISION",
    "EXTENSION_REQUEST",
    "PAUSE_REQUEST",
    "BLOCKER_REPORT",
    "REASSIGN",
    "WORKLOAD_ADJUST",
    "CANCEL",
    "QUALITY_ISSUE",
    "SELF_REPORT",
}

TASK_ATTACHMENT_KINDS = {"EVIDENCE", "SUBMISSION", "OTHER"}

TASK_PAUSE_REASONS = {
    "WAITING_CITIZEN",   # Chờ người dân/doanh nghiệp bổ sung hồ sơ, nghĩa vụ tài chính
    "WAITING_AGENCY",    # Chờ cơ quan/đơn vị phối hợp
    "SYSTEM_ERROR",      # Lỗi hệ thống
    "FORCE_MAJEURE",     # Bất khả kháng
    "APPROVED_OTHER",    # Tạm dừng hợp lệ khác theo quyết định cấp có thẩm quyền
}

RECURRENCE_INTERVALS = {"DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"}

# --- Danh mục sản phẩm / KPI ---

CATALOG_STATUSES = {"DRAFT", "PILOT", "OFFICIAL"}

KPI_CRITERION_KINDS = {
    "GENERAL_GROUP",       # Nhóm tiêu chí chung (cha) — áp dụng chung, không phân biệt quản lý/không quản lý
    "GENERAL_ITEM",        # Tiêu chí con thuộc nhóm chung — định tính
    "TASK_QUANTITY",       # Số lượng — định lượng, tự tính từ tasks
    "TASK_QUALITY",        # Chất lượng — định lượng, tự tính từ tasks
    "TASK_PROGRESS",       # Tiến độ — định lượng, tự tính từ tasks
    "STAFF_RESULTS",       # Nhóm kết quả nhiệm vụ CHỈ áp dụng viên chức KHÔNG giữ chức vụ quản lý (cha SL/CL/TĐ)
    "MANAGER_PERSONAL",    # Nhóm (a) kết quả cá nhân CHỈ áp dụng viên chức quản lý (cha SL/CL/TĐ riêng)
    "MANAGER_UNIT",        # Nhóm (b) kết quả đơn vị/lĩnh vực phụ trách — định tính, mức đạt 100/50/0%
    "MANAGER_ORG_CAPABILITY",  # Nhóm (c) khả năng tổ chức triển khai — định tính
    "MANAGER_COHESION",    # Nhóm (d) năng lực tập hợp, đoàn kết — định tính
}

# Nhóm cha đánh dấu nhánh CHỈ áp dụng cho một loại vị trí — compute_score phải
# bỏ qua nhánh không khớp với is_managerial_snapshot của người được chấm.
KPI_MANAGERIAL_ONLY_KINDS = {"MANAGER_PERSONAL", "MANAGER_UNIT", "MANAGER_ORG_CAPABILITY", "MANAGER_COHESION"}
KPI_NON_MANAGERIAL_ONLY_KINDS = {"STAFF_RESULTS"}

KPI_FORMULA_KEYS = {"QUANTITY_RATIO", "QUALITY_RATIO", "PROGRESS_RATIO"}

KPI_PERIOD_TYPES = {"MONTH", "QUARTER", "YEAR"}

KPI_PERIOD_STATUSES = {"OPEN", "LOCKED", "REOPENED"}

KPI_SCORE_STATUSES = {
    "DRAFT",
    "SELF_ASSESSED",
    "REVIEWED",
    "AGGREGATED",
    "APPROVED",
    "NOT_RATED",  # chưa đủ điều kiện/thời gian xếp loại (mục 15.4) — KHÔNG phải "không hoàn thành"
}

KPI_EVALUATION_COMMENT_TYPES = {
    "MEETING_MINUTES",       # Biên bản họp nhận xét, đánh giá (Mẫu 13)
    "PARTY_COMMITTEE_INPUT", # Ý kiến cấp ủy đảng (chỉ viên chức quản lý)
    "STAKEHOLDER_INPUT",     # Ý kiến đóng góp khác
    "EXPLANATION",           # Giải trình của viên chức
    "ADJUSTMENT_REQUEST",    # Phiếu đề nghị điều chỉnh kết quả (Mẫu 14)
}

NOTIFICATION_TYPES = {
    "TASK_ASSIGNED",
    "TASK_DEADLINE_CHANGED",
    "TASK_DUE_SOON",
    "TASK_OVERDUE",
    "TASK_SUBMITTED",
    "TASK_RETURNED",
    "TASK_BLOCKED",
    "KPI_EXPLANATION_REQUEST",
    "KPI_SCORE_READY",
    "KPI_PERIOD_LOCKED",
}
