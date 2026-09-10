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

## Vai trò mẫu (bảng `roles`, `is_system = true`)

| Mã vai trò | Quyền | Ghi chú |
|---|---|---|
| `SYSTEM_ADMIN` | **tất cả** (gồm `goiso.*`) | Toàn quyền platform |
| `HR_ADMIN` | nhóm `employee.*`, `unit.*`, `position.*`, `audit.view` | Quản trị nhân sự toàn hệ |
| `UNIT_MANAGER` | `employee.view/create/update/transfer`, `unit.view`, `position.view` | Giới hạn theo phạm vi đơn vị (`user_unit_scopes`) |
| `VIEWER` | `employee.view`, `unit.view`, `position.view` | Chỉ đọc |
| `GOISO_ADMIN` | `goiso.view`, `goiso.counter`, `goiso.admin`, `unit.view` | Quản trị gọi số **toàn hệ thống** |
| `GOISO_BRANCH_ADMIN` | `goiso.view`, `goiso.counter`, `goiso.admin` | Quản trị gọi số **trong phạm vi chi nhánh được cấp** |
| **`GOISO_COUNTER`** | `goiso.view`, `goiso.counter` | **Tài khoản được giao trực một cửa/quầy** — vào được trang gọi số của chi nhánh mình |

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
