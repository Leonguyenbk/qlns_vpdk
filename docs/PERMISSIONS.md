# PERMISSIONS — Quyền & vai trò của platform

Backend **luôn** kiểm tra quyền (decorator `@require_permission` cho nhân sự,
`admin_required` / `counter_guard` cho goiso). Ẩn nút ở frontend chỉ là phụ.

## Quyền (bảng `permissions`)

### Nhân sự
| Mã | Ý nghĩa |
|---|---|
| `employee.view` / `employee.view_sensitive` | Xem hồ sơ / xem CCCD… |
| `employee.create` / `update` / `delete` / `restore` | CRUD hồ sơ nhân sự |
| `employee.transfer` / `employee.history_adjust` | Chuyển đơn vị / sửa lịch sử |
| `unit.view` / `unit.manage` | Xem / quản lý cơ cấu đơn vị |
| `position.view` / `position.manage` | Xem / quản lý chức vụ (gồm giới hạn chức vụ đơn nhất) |
| `user.view` / `user.manage` | Xem / quản lý tài khoản, gán vai trò & phạm vi |
| `role.view` / `role.manage` | Xem / quản lý vai trò – quyền |
| `audit.view` | Xem nhật ký |

### Gọi số (goiso) — thêm ở Phase 5
| Mã | Ý nghĩa |
|---|---|
| `goiso.view` | Xem hàng đợi, màn hình, bảng chờ, thống kê |
| `goiso.counter` | **Trực một cửa/quầy**: gọi số, gọi lại, bỏ qua, hoàn thành |
| `goiso.admin` | Cấu hình dịch vụ/quầy/màn hình, chi nhánh, thiết bị kiosk, đặt lịch |

### Giao việc – Theo dõi nhiệm vụ
| Mã | Ý nghĩa |
|---|---|
| `task.view_own` | Xem nhiệm vụ của bản thân ("Công việc của tôi") |
| `task.view_all` | Xem toàn bộ nhiệm vụ trong phạm vi đơn vị được phân quyền (tổng quan điều hành) |
| `task.create` | Tạo nhiệm vụ / giao việc |
| `task.assign` | Giao việc cho người/đơn vị khác, phân việc lại, thêm/gỡ người thực hiện |
| `task.manage` | Sửa/hủy/gia hạn/điều chỉnh khối lượng nhiệm vụ, xác nhận thời gian tạm dừng |
| `task.accept` | Nghiệm thu, phê duyệt kết quả, trả lại yêu cầu làm lại |
| `task.template_manage` | Quản lý mẫu nhiệm vụ |

### Đánh giá KPI (dự thảo/thí điểm — xem `docs/TASK_KPI_ANALYSIS.md`)
| Mã | Ý nghĩa |
|---|---|
| `kpi.view_own` | Xem KPI của bản thân |
| `kpi.view_all` | Xem KPI trong phạm vi được phân quyền |
| `kpi.self_assess` | Tự đánh giá, tự nhận mức xếp loại |
| `kpi.review` | Theo dõi, đánh giá trực tiếp (khoản 2 Điều 13 NĐ 233/2026) |
| `kpi.aggregate` | Tổng hợp (bộ phận tổ chức cán bộ) |
| `kpi.approve` | Quyết định xếp loại + khoá kỳ (khoản 3 Điều 13 — tập trung ở Giám đốc VPĐKĐĐ) |
| `kpi.criteria_manage` | Quản lý bộ tiêu chí, danh mục sản phẩm, hệ số Kn/CAP |
| `kpi.period_manage` | Mở/khoá/mở lại kỳ đánh giá |
| `kpi.adjust` | Điều chỉnh/thay thế kết quả đã khoá (Mẫu số 15) |

## Vai trò mẫu (bảng `roles`, `is_system = true`)

| Mã vai trò | Quyền | Ghi chú |
|---|---|---|
| `SYSTEM_ADMIN` | **tất cả** (gồm `goiso.*`, `task.*`, `kpi.*`) | Toàn quyền kỹ thuật platform — **khuyến nghị KHÔNG dùng làm người phê duyệt KPI nghiệp vụ chính thức** trong thực tế (xem mục 4.7 `TASK_KPI_ANALYSIS.md`) |
| `HR_ADMIN` | nhóm `employee.*`, `unit.*`, `position.*`, `audit.view` + tự phục vụ (`task.view_own`/`kpi.view_own`/`kpi.self_assess`) | Quản trị nhân sự toàn hệ |
| `UNIT_MANAGER` | `employee.view/create/update/transfer`, `unit.view`, `position.view` + tự phục vụ | Giới hạn theo phạm vi đơn vị (`user_unit_scopes`) |
| `VIEWER` | `employee.view`, `unit.view`, `position.view` + tự phục vụ | Chỉ đọc |
| `GOISO_ADMIN` / `GOISO_BRANCH_ADMIN` / `GOISO_COUNTER` | như cũ + tự phục vụ | Quản trị/trực quầy gọi số |
| **`OFFICE_LEADER`** | `task.view_all/create/assign/manage/accept`, `kpi.view_all/review/approve/period_manage/adjust/criteria_manage` | Lãnh đạo Văn phòng — thẩm quyền xếp loại tập trung (khoản 3 Điều 13) |
| **`ORG_PERSONNEL`** | `task.view_all/template_manage`, `kpi.view_all/aggregate/criteria_manage/period_manage` | Bộ phận tổ chức cán bộ — tổng hợp, quản lý danh mục/bộ tiêu chí |
| **`UNIT_HEAD`** | `task.view_all/create/assign/manage/accept`, `kpi.view_all/review` (phạm vi theo `user_unit_scopes`) | Lãnh đạo phòng/chi nhánh |
| **`TASK_ASSIGNER`** | `task.view_all/create/assign/accept` (phạm vi theo `user_unit_scopes`) | Người được uỷ quyền giao việc/nghiệm thu, không nhất thiết là lãnh đạo |

Mọi tài khoản có hồ sơ nhân sự (`users.employee_id` khác NULL) và giữ bất kỳ
vai trò nào ở trên đều thấy được trang cá nhân "Công việc của tôi"/"KPI của
tôi" nhờ quyền `task.view_own`/`kpi.view_own`/`kpi.self_assess` được gắn kèm
theo từng vai trò (migration `0008_task_kpi_permissions`).

## "Ai được vào trang gọi số?"

Trang `/b/<chi-nhánh>/counter` và các API `/api/b/<chi-nhánh>/counter/*` đi qua
`counter_guard`:

1. Phải đăng nhập (JWT — cookie hoặc Bearer).
2. Phải có `goiso.counter` (tức vai trò `GOISO_COUNTER`, `GOISO_BRANCH_ADMIN`,
   `GOISO_ADMIN` hoặc `SYSTEM_ADMIN`).
3. Nếu **không** phải quản trị gọi số: chi nhánh trên URL phải khớp
   `users.goiso_branch_code` của tài khoản. Sai chi nhánh → 403.

Kiosk vật lý (máy bốc số) **không** dùng tài khoản — vẫn xác thực bằng
`X-Branch-Key` (khoá riêng mỗi chi nhánh), không đổi.

## Gán tài khoản trực quầy

- Web: `POST /api/users` (quyền `user.manage`) → tạo user, gán vai trò
  `GOISO_COUNTER`, đặt `goiso_branch_code`. (UI ở Phase 7.)
- Di trú hàng loạt từ hệ goiso cũ: `python -m scripts.migrate_goiso_users --commit`
  — mỗi nhân viên goiso → user cùng tên + vai trò `GOISO_COUNTER` +
  `goiso_branch_code`, giữ mật khẩu sha256 cũ ở `legacy_password_sha256`
  (lần đăng nhập đầu tự nâng cấp Argon2).

> Phase 6: `goiso_branch_code` sẽ được thay bằng liên kết trực tiếp
> `organization_units` ↔ chi nhánh goiso; khi đó phạm vi trực quầy dùng chung
> cơ chế `user_unit_scopes` với nhân sự.
