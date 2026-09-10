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

```bash
flask --app wsgi db upgrade      # nâng cấp
flask --app wsgi db downgrade -1 # lùi 1 bước
```

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
