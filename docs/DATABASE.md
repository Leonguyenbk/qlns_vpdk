# DATABASE — Một CSDL MySQL dùng chung

Từ Phase 6, cả platform dùng **một CSDL MySQL 8** (`personnel_management` khi
triển khai trên máy hiện tại). Bảng phân theo tiền tố:

| Nhóm | Bảng |
|---|---|
| Auth / RBAC | `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `user_unit_scopes`, `refresh_tokens` |
| Tổ chức (dùng chung) | `organization_units` — cây đơn vị; cột `goiso_branch_code` liên kết sang chi nhánh gọi số |
| Nhân sự | `employees`, `employee_assignments`, `employee_education`, `job_grades`, `positions`, `unit_position_limits` |
| Nhật ký | `audit_logs` |
| **Gọi số** | `goiso_branches`, `goiso_queue`, `goiso_counters_status`, `goiso_config`, `goiso_visitor_stats`, `goiso_appointments`, `goiso_devices` |
| **Giao việc** | `tasks`, `task_assignments`, `task_pauses`, `task_logs`, `task_attachments`, `task_templates` |
| **KPI / danh mục sản phẩm** | `product_catalog_groups`, `products`, `product_conversions`, `kpi_criteria_sets`, `kpi_criteria`, `kpi_periods`, `kpi_scores`, `kpi_score_details`, `kpi_evaluation_comments` |
| Thông báo | `notifications` |

- `goiso_config.branch_id = 0` → cấu hình toàn cục (vd `kiosk_release`).
- `goiso_branches.id` được giữ NGUYÊN từ hệ cũ để `goiso_queue.branch_id`… không đứt tham chiếu.
- `users.goiso_branch_code` (tạm) trỏ tài khoản trực quầy về `goiso_branches.code`.
  `users.legacy_password_sha256` giữ hash goiso cũ, tự nâng cấp Argon2 ở lần đăng nhập đầu.

## Migration (Alembic)

| Rev | Nội dung |
|---|---|
| 0001–0004 | Schema nhân sự giai đoạn 1 |
| **0005** | Quyền/vai trò `GOISO_*`; cột `users.goiso_branch_code`, `users.legacy_password_sha256` |
| **0006** | Bảng `goiso_*`; cột `organization_units.goiso_branch_code` |
| **0007** | Bảng Giao việc + KPI (xem danh mục ở trên); seed 18 nhóm sản phẩm `product_catalog_groups` (dữ liệu tham chiếu trích từ Phụ lục II tài liệu dự thảo KPI VPĐKĐĐ — không phải dữ liệu demo) |
| **0008** | Quyền/vai trò `task.*`/`kpi.*`; vai trò mới `OFFICE_LEADER`, `ORG_PERSONNEL`, `UNIT_HEAD`, `TASK_ASSIGNER`; bổ sung quyền tự phục vụ (`task.view_own`/`kpi.view_own`/`kpi.self_assess`) cho các vai trò sẵn có |

```bash
flask --app wsgi db upgrade      # nâng cấp — chạy 1 lần, áp dụng tuần tự 0007 rồi 0008
flask --app wsgi db downgrade -1 # lùi 1 bước
```

Cả hai migration 0007/0008 chỉ **thêm** bảng/cột/quyền mới, kiểm tra tồn tại
trước khi tạo (idempotent) và không xoá/sửa dữ liệu nhân sự, gọi số hay tài
khoản hiện có. An toàn để chạy trên CSDL đang có dữ liệu thật.

## Tầng dữ liệu goiso

`app/modules/goiso/legacy_db.py` giữ SQL thô (như bản SQLite gốc) nhưng chạy qua
một **shim SQLAlchemy** (`get_conn()`): `?`→bind params, và `ON CONFLICT(...) DO
UPDATE` (SQLite) tự dịch sang `ON DUPLICATE KEY UPDATE` (MySQL). Việc viết lại
sang ORM/repository làm dần ở các phase sau — ưu tiên ổn định.

## Sao lưu trước khi nâng cấp

```bash
mysqldump -u <user> -p --single-transaction --no-tablespaces --routines --triggers \
  --databases personnel_management > backup_YYYYMMDD.sql
```

## Khôi phục (nếu migration lỗi hoặc cần lùi lại)

```bash
# 1. Dừng dịch vụ backend (NSSM) trước khi khôi phục để tránh ghi đè trong lúc restore
nssm stop <ten-service-backend>

# 2. Khôi phục từ bản sao lưu gần nhất
mysql -u <user> -p personnel_management < backup_YYYYMMDD.sql

# 3. Kiểm tra phiên bản migration hiện tại của CSDL vừa khôi phục
flask --app wsgi db current

# 4. Khởi động lại dịch vụ
nssm start <ten-service-backend>
```

Luôn sao lưu (`mysqldump`) ngay trước khi chạy `flask db upgrade` cho một
migration mới trên CSDL sản xuất — kể cả migration được viết idempotent/an
toàn như 0007–0008, đây vẫn là quy tắc bắt buộc trước mọi thay đổi schema.
