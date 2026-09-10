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
};
