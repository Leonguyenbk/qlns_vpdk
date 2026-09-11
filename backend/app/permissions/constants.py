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

# --- Nhóm quyền Gọi số / Kiosk (module goiso) ---
GOISO_VIEW = "goiso.view"        # xem hàng đợi, màn hình, bảng chờ, thống kê
GOISO_COUNTER = "goiso.counter"  # trực một cửa/quầy: gọi số, gọi lại, bỏ qua, hoàn thành
GOISO_ADMIN = "goiso.admin"      # cấu hình dịch vụ/quầy/màn hình, chi nhánh, thiết bị, đặt lịch

# --- Nhóm quyền Giao việc / Theo dõi nhiệm vụ ---
TASK_VIEW_OWN = "task.view_own"      # xem nhiệm vụ của bản thân (chủ trì/phối hợp)
TASK_VIEW_ALL = "task.view_all"      # xem toàn bộ nhiệm vụ trong phạm vi đơn vị được phân quyền (tổng quan điều hành)
TASK_CREATE = "task.create"          # tạo nhiệm vụ / giao việc
TASK_ASSIGN = "task.assign"          # giao việc cho người khác, đơn vị khác, phân việc lại
TASK_MANAGE = "task.manage"          # sửa/hủy/gia hạn/điều chỉnh khối lượng nhiệm vụ bất kỳ trong phạm vi
TASK_ACCEPT = "task.accept"          # nghiệm thu, phê duyệt kết quả, trả lại yêu cầu làm lại
TASK_TEMPLATE_MANAGE = "task.template_manage"  # quản lý mẫu nhiệm vụ, danh mục sản phẩm dùng khi giao việc

# --- Nhóm quyền Đánh giá KPI ---
KPI_VIEW_OWN = "kpi.view_own"            # xem KPI của bản thân
KPI_VIEW_ALL = "kpi.view_all"            # xem KPI toàn bộ/đơn vị trong phạm vi được phân quyền
KPI_SELF_ASSESS = "kpi.self_assess"      # viên chức tự đánh giá, tự nhận mức xếp loại
KPI_REVIEW = "kpi.review"                # người phụ trách trực tiếp theo dõi, đánh giá (khoản 2 Điều 13)
KPI_AGGREGATE = "kpi.aggregate"          # bộ phận tổ chức cán bộ tổng hợp
KPI_APPROVE = "kpi.approve"              # cấp có thẩm quyền quyết định xếp loại + khoá kỳ (khoản 3 Điều 13)
KPI_CRITERIA_MANAGE = "kpi.criteria_manage"  # quản lý bộ tiêu chí, danh mục sản phẩm, hệ số Kn/CAP
KPI_PERIOD_MANAGE = "kpi.period_manage"  # mở/khoá/mở lại kỳ đánh giá
KPI_ADJUST = "kpi.adjust"                # điều chỉnh/thay thế kết quả đã khoá (Mẫu số 15)


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
    (GOISO_VIEW, "Gọi số: xem hàng đợi, màn hình, bảng chờ, thống kê"),
    (GOISO_COUNTER, "Gọi số: trực một cửa/quầy (gọi, gọi lại, bỏ qua, hoàn thành)"),
    (GOISO_ADMIN, "Gọi số: cấu hình dịch vụ/quầy/màn hình, chi nhánh, thiết bị, đặt lịch"),
    (TASK_VIEW_OWN, "Giao việc: xem nhiệm vụ của bản thân"),
    (TASK_VIEW_ALL, "Giao việc: xem toàn bộ nhiệm vụ trong phạm vi được phân quyền"),
    (TASK_CREATE, "Giao việc: tạo nhiệm vụ / giao việc"),
    (TASK_ASSIGN, "Giao việc: giao việc cho người khác/đơn vị khác, phân việc lại"),
    (TASK_MANAGE, "Giao việc: sửa, hủy, gia hạn, điều chỉnh khối lượng nhiệm vụ"),
    (TASK_ACCEPT, "Giao việc: nghiệm thu, phê duyệt kết quả, trả lại yêu cầu làm lại"),
    (TASK_TEMPLATE_MANAGE, "Giao việc: quản lý mẫu nhiệm vụ và danh mục sản phẩm"),
    (KPI_VIEW_OWN, "KPI: xem kết quả đánh giá của bản thân"),
    (KPI_VIEW_ALL, "KPI: xem kết quả đánh giá trong phạm vi được phân quyền"),
    (KPI_SELF_ASSESS, "KPI: tự đánh giá, tự nhận mức xếp loại"),
    (KPI_REVIEW, "KPI: theo dõi, đánh giá (người phụ trách trực tiếp)"),
    (KPI_AGGREGATE, "KPI: tổng hợp (bộ phận tổ chức cán bộ)"),
    (KPI_APPROVE, "KPI: quyết định xếp loại và khoá kỳ (cấp có thẩm quyền)"),
    (KPI_CRITERIA_MANAGE, "KPI: quản lý bộ tiêu chí, danh mục sản phẩm, hệ số Kn/CAP"),
    (KPI_PERIOD_MANAGE, "KPI: mở/khoá/mở lại kỳ đánh giá"),
    (KPI_ADJUST, "KPI: điều chỉnh/thay thế kết quả đã khoá"),
]

ALL_PERMISSIONS = [code for code, _ in PERMISSION_DEFINITIONS]


# Vai trò mẫu -> danh sách permission
ROLE_SYSTEM_ADMIN = "SYSTEM_ADMIN"
ROLE_HR_ADMIN = "HR_ADMIN"
ROLE_UNIT_MANAGER = "UNIT_MANAGER"
ROLE_VIEWER = "VIEWER"

# Vai trò module Gọi số
ROLE_GOISO_ADMIN = "GOISO_ADMIN"                # quản trị gọi số toàn hệ thống
ROLE_GOISO_BRANCH_ADMIN = "GOISO_BRANCH_ADMIN"  # quản trị gọi số trong phạm vi chi nhánh được cấp
ROLE_GOISO_COUNTER = "GOISO_COUNTER"            # được giao TRỰC MỘT CỬA/QUẦY, vào trang gọi số

# Vai trò module Giao việc / KPI (mục 9, 17 tài liệu dự thảo)
ROLE_OFFICE_LEADER = "OFFICE_LEADER"      # Lãnh đạo Văn phòng ĐKĐĐ — thẩm quyền xếp loại tập trung (khoản 3 Điều 13)
ROLE_ORG_PERSONNEL = "ORG_PERSONNEL"      # Bộ phận tổ chức cán bộ — tổng hợp, quản lý danh mục/tiêu chí
ROLE_UNIT_HEAD = "UNIT_HEAD"              # Lãnh đạo phòng/chi nhánh — theo dõi, giao việc trong phạm vi đơn vị
ROLE_TASK_ASSIGNER = "TASK_ASSIGNER"      # Người được uỷ quyền giao việc/nghiệm thu (không nhất thiết là lãnh đạo)

# Quyền tự phục vụ tối thiểu — mọi tài khoản có hồ sơ nhân sự đều cần để dùng
# trang "Công việc của tôi" (mục 5), bất kể đang giữ vai trò module nào khác.
_STAFF_SELF_SERVICE = [TASK_VIEW_OWN, KPI_VIEW_OWN, KPI_SELF_ASSESS]

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
            *_STAFF_SELF_SERVICE,
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
            *_STAFF_SELF_SERVICE,
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
            *_STAFF_SELF_SERVICE,
        ],
    },
    ROLE_GOISO_ADMIN: {
        "name": "Quản trị Gọi số",
        "description": "Toàn quyền module gọi số: cấu hình dịch vụ/quầy/màn hình, "
        "chi nhánh, thiết bị kiosk, đặt lịch trên toàn hệ thống.",
        "is_system": True,
        "permissions": [GOISO_VIEW, GOISO_COUNTER, GOISO_ADMIN, UNIT_VIEW, *_STAFF_SELF_SERVICE],
    },
    ROLE_GOISO_BRANCH_ADMIN: {
        "name": "Quản trị Gọi số chi nhánh",
        "description": "Quản trị gọi số trong phạm vi chi nhánh được phân công "
        "(cấu hình dịch vụ/quầy/màn hình, trực quầy). Phạm vi giới hạn theo đơn vị.",
        "is_system": True,
        "permissions": [GOISO_VIEW, GOISO_COUNTER, GOISO_ADMIN, *_STAFF_SELF_SERVICE],
    },
    ROLE_GOISO_COUNTER: {
        "name": "Nhân viên Gọi số (trực cửa)",
        "description": "Được giao trực một cửa/quầy: vào trang gọi số, gọi số, gọi lại, "
        "bỏ qua, hoàn thành. Chỉ thao tác trong chi nhánh được phân công.",
        "is_system": True,
        "permissions": [GOISO_VIEW, GOISO_COUNTER, *_STAFF_SELF_SERVICE],
    },
    ROLE_OFFICE_LEADER: {
        "name": "Lãnh đạo Văn phòng",
        "description": "Giám đốc/Phó Giám đốc VPĐKĐĐ: giao việc, nghiệm thu, xem toàn bộ "
        "nhiệm vụ và KPI, quyết định xếp loại chất lượng và khoá kỳ đánh giá "
        "(thẩm quyền tập trung theo khoản 3 Điều 13 Nghị định số 233/2026/NĐ-CP).",
        "is_system": True,
        "permissions": [
            TASK_VIEW_ALL, TASK_CREATE, TASK_ASSIGN, TASK_MANAGE, TASK_ACCEPT,
            KPI_VIEW_ALL, KPI_REVIEW, KPI_APPROVE, KPI_PERIOD_MANAGE, KPI_ADJUST,
            KPI_CRITERIA_MANAGE, UNIT_VIEW, EMPLOYEE_VIEW,
            *_STAFF_SELF_SERVICE,
        ],
    },
    ROLE_ORG_PERSONNEL: {
        "name": "Bộ phận tổ chức cán bộ",
        "description": "Tham mưu tổng hợp: quản lý danh mục sản phẩm/bộ tiêu chí, "
        "tổng hợp kết quả theo dõi đánh giá, chuẩn bị hồ sơ trình cấp có thẩm quyền.",
        "is_system": True,
        "permissions": [
            TASK_VIEW_ALL, TASK_TEMPLATE_MANAGE,
            KPI_VIEW_ALL, KPI_AGGREGATE, KPI_CRITERIA_MANAGE, KPI_PERIOD_MANAGE,
            UNIT_VIEW, EMPLOYEE_VIEW,
            *_STAFF_SELF_SERVICE,
        ],
    },
    ROLE_UNIT_HEAD: {
        "name": "Lãnh đạo phòng/chi nhánh",
        "description": "Trưởng phòng/Giám đốc Chi nhánh (hoặc cấp phó): giao việc, theo dõi, "
        "nghiệm thu trong phạm vi đơn vị được phân công (phạm vi lọc theo user_unit_scopes).",
        "is_system": True,
        "permissions": [
            TASK_VIEW_ALL, TASK_CREATE, TASK_ASSIGN, TASK_MANAGE, TASK_ACCEPT,
            KPI_VIEW_ALL, KPI_REVIEW,
            UNIT_VIEW, EMPLOYEE_VIEW,
            *_STAFF_SELF_SERVICE,
        ],
    },
    ROLE_TASK_ASSIGNER: {
        "name": "Người được giao quyền giao việc/nghiệm thu",
        "description": "Được uỷ quyền giao việc và nghiệm thu trong phạm vi cụ thể mà "
        "không nhất thiết là lãnh đạo đơn vị (mục 9 — quyền cấp qua user_unit_scopes).",
        "is_system": True,
        "permissions": [
            TASK_VIEW_ALL, TASK_CREATE, TASK_ASSIGN, TASK_ACCEPT,
            UNIT_VIEW, EMPLOYEE_VIEW,
            *_STAFF_SELF_SERVICE,
        ],
    },
}
