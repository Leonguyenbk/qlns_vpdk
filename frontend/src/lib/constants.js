// Nhãn tiếng Việt cho các giá trị enum của backend

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

export const EMPLOYEE_STATUS_LABELS = {
  WORKING: "Đang làm việc",
  ON_LEAVE: "Nghỉ phép",
  RETIRED: "Nghỉ hưu",
  RESIGNED: "Đã nghỉ việc",
  TRANSFERRED: "Đã chuyển công tác",
  INACTIVE: "Ngừng hoạt động",
};

export const EMPLOYEE_STATUS_BADGE = {
  WORKING: "badge-ok",
  ON_LEAVE: "badge-warn",
  RETIRED: "badge-neutral",
  RESIGNED: "badge-danger",
  TRANSFERRED: "badge-info",
  INACTIVE: "badge-neutral",
};

export const EMPLOYMENT_TYPE_LABELS = {
  OFFICIAL: "Chính thức",
  CONTRACT: "Hợp đồng",
  PROBATION: "Thử việc",
  COLLABORATOR: "Cộng tác viên",
  SECONDED: "Biệt phái",
};

export const GENDER_LABELS = { MALE: "Nam", FEMALE: "Nữ", OTHER: "Khác" };

export const UNIT_TYPE_LABELS = {
  HEAD_OFFICE: "Trụ sở chính",
  DEPARTMENT: "Phòng chuyên môn",
  BRANCH: "Chi nhánh",
  SECTION: "Bộ phận",
};

export const ASSIGNMENT_TYPE_LABELS = {
  RECRUITMENT: "Tuyển dụng",
  APPOINTMENT: "Bổ nhiệm",
  TRANSFER: "Chuyển đơn vị",
  SECONDMENT: "Biệt phái",
  REASSIGNMENT: "Điều động",
};

export const PERMISSIONS = {
  EMPLOYEE_VIEW: "employee.view",
  EMPLOYEE_VIEW_SENSITIVE: "employee.view_sensitive",
  EMPLOYEE_CREATE: "employee.create",
  EMPLOYEE_UPDATE: "employee.update",
  EMPLOYEE_DELETE: "employee.delete",
  EMPLOYEE_RESTORE: "employee.restore",
  EMPLOYEE_TRANSFER: "employee.transfer",
  EMPLOYEE_HISTORY_ADJUST: "employee.history_adjust",
  UNIT_VIEW: "unit.view",
  UNIT_MANAGE: "unit.manage",
  POSITION_VIEW: "position.view",
  POSITION_MANAGE: "position.manage",
  USER_VIEW: "user.view",
  USER_MANAGE: "user.manage",
  ROLE_VIEW: "role.view",
  ROLE_MANAGE: "role.manage",
  AUDIT_VIEW: "audit.view",
  GOISO_VIEW: "goiso.view",
  GOISO_COUNTER: "goiso.counter",
  GOISO_ADMIN: "goiso.admin",
  // Giao việc
  TASK_VIEW_OWN: "task.view_own",
  TASK_VIEW_ALL: "task.view_all",
  TASK_CREATE: "task.create",
  TASK_ASSIGN: "task.assign",
  TASK_MANAGE: "task.manage",
  TASK_ACCEPT: "task.accept",
  TASK_TEMPLATE_MANAGE: "task.template_manage",
  // KPI
  KPI_VIEW_OWN: "kpi.view_own",
  KPI_VIEW_ALL: "kpi.view_all",
  KPI_SELF_ASSESS: "kpi.self_assess",
  KPI_REVIEW: "kpi.review",
  KPI_AGGREGATE: "kpi.aggregate",
  KPI_APPROVE: "kpi.approve",
  KPI_CRITERIA_MANAGE: "kpi.criteria_manage",
  KPI_PERIOD_MANAGE: "kpi.period_manage",
  KPI_ADJUST: "kpi.adjust",
  // Khảo sát
  SURVEY_VIEW: "survey.view",
  SURVEY_CREATE: "survey.create",
  SURVEY_UPDATE: "survey.update",
  SURVEY_DELETE: "survey.delete",
  SURVEY_MANAGE_QUESTIONS: "survey.manage_questions",
  SURVEY_VIEW_STATISTICS: "survey.view_statistics",
  SURVEY_EXPORT: "survey.export",
  SURVEY_MANAGE_ALL_BRANCHES: "survey.manage_all_branches",
};

// Nhóm quyền để cổng ứng dụng quyết định hiện thẻ module nào
export const MODULE_PERMS = {
  NHANSU: ["employee.view", "unit.view", "position.view"],
  GOISO: ["goiso.view", "goiso.counter", "goiso.admin"],
  ADMIN: ["user.view", "role.view", "audit.view"],
  TASKS: ["task.view_own", "task.view_all", "task.create", "task.assign", "task.manage", "task.accept"],
  KPI: ["kpi.view_own", "kpi.view_all", "kpi.criteria_manage", "kpi.period_manage"],
  // Trang Công việc (gộp Giao việc + KPI) — dùng chung cho sidebar, route và thẻ ở cổng ứng dụng
  WORK: ["task.view_all", "task.view_own", "task.create", "task.assign", "kpi.view_own"],
};

// ---- Giao việc – Theo dõi nhiệm vụ ----

export const TASK_STATUS_LABELS = {
  DRAFT: "Nháp",
  ASSIGNED: "Đã giao",
  IN_PROGRESS: "Đang thực hiện",
  PENDING_COLLAB: "Chờ phối hợp",
  PAUSED: "Tạm dừng",
  NEEDS_REVISION: "Yêu cầu bổ sung/làm lại",
  PENDING_ACCEPTANCE: "Chờ nghiệm thu",
  COMPLETED: "Hoàn thành",
  CANCELLED: "Đã hủy",
};

export const TASK_STATUS_BADGE = {
  DRAFT: "badge-neutral",
  ASSIGNED: "badge-info",
  IN_PROGRESS: "badge-info",
  PENDING_COLLAB: "badge-warn",
  PAUSED: "badge-warn",
  NEEDS_REVISION: "badge-danger",
  PENDING_ACCEPTANCE: "badge-warn",
  COMPLETED: "badge-ok",
  CANCELLED: "badge-neutral",
};

export const TASK_PRIORITY_LABELS = {
  LOW: "Thấp",
  NORMAL: "Bình thường",
  HIGH: "Cao",
  URGENT: "Khẩn cấp",
};

export const TASK_SOURCE_LABELS = {
  PLAN: "Kế hoạch",
  DIRECTIVE: "Chỉ đạo",
  ROUTINE: "Thường xuyên",
  CASE_FILE: "Hồ sơ vụ việc",
  AD_HOC: "Đột xuất",
};

export const TASK_DEADLINE_TYPE_LABELS = {
  INTERNAL: "Nội bộ",
  TTHC: "Thủ tục hành chính",
};

export const TASK_PAUSE_REASON_LABELS = {
  WAITING_CITIZEN: "Chờ người dân/doanh nghiệp bổ sung hồ sơ",
  WAITING_AGENCY: "Chờ cơ quan/đơn vị phối hợp",
  SYSTEM_ERROR: "Lỗi hệ thống",
  FORCE_MAJEURE: "Bất khả kháng",
  APPROVED_OTHER: "Tạm dừng khác (có quyết định)",
};

// ---- Đánh giá KPI ----

export const KPI_SCORE_STATUS_LABELS = {
  DRAFT: "Nháp — chờ tính điểm",
  SELF_ASSESSED: "Đã tự đánh giá",
  REVIEWED: "Đã theo dõi, đánh giá",
  AGGREGATED: "Đã tổng hợp",
  APPROVED: "Đã phê duyệt chính thức",
  NOT_RATED: "Không xếp loại",
};

export const KPI_SCORE_STATUS_BADGE = {
  DRAFT: "badge-neutral",
  SELF_ASSESSED: "badge-info",
  REVIEWED: "badge-info",
  AGGREGATED: "badge-warn",
  APPROVED: "badge-ok",
  NOT_RATED: "badge-neutral",
};

export const CATALOG_STATUS_LABELS = {
  DRAFT: "Dự thảo",
  PILOT: "Thí điểm",
  OFFICIAL: "Chính thức",
};

// ---- Khảo sát – Đánh giá mức độ hài lòng ----

export const SURVEY_STATUS_LABELS = {
  draft: "Nháp",
  active: "Đang hoạt động",
  paused: "Tạm khóa",
  closed: "Đã đóng",
  archived: "Lưu trữ",
};

export const SURVEY_STATUS_BADGE = {
  draft: "badge-neutral",
  active: "badge-ok",
  paused: "badge-warn",
  closed: "badge-info",
  archived: "badge-neutral",
};

export const QUESTION_TYPE_LABELS = {
  single_choice: "Một lựa chọn",
  multiple_choice: "Nhiều lựa chọn",
  yes_no: "Có / Không",
  rating: "Đánh giá 1–5",
  text: "Văn bản ngắn",
  textarea: "Văn bản dài",
  number: "Số",
  date: "Ngày",
};

export const QUESTION_TYPES_WITH_OPTIONS = new Set(["single_choice", "multiple_choice"]);

export const RATING_LEVEL_LABELS = {
  5: "Rất hài lòng",
  4: "Hài lòng",
  3: "Bình thường",
  2: "Không hài lòng",
  1: "Rất không hài lòng",
};

export const DATE_PRESET_LABELS = {
  today: "Hôm nay",
  "7d": "7 ngày",
  "30d": "30 ngày",
  this_month: "Tháng này",
  this_quarter: "Quý này",
  this_year: "Năm nay",
};
