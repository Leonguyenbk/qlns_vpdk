# ARCHITECTURE — Platform hợp nhất

```
                         Cloudflare Tunnel (1 hostname / hoặc nhiều -> cùng đích)
                                        │
                              waitress  :5050  (một tiến trình)
                                        │  wsgi:app  = create_app()
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
   Portal + SPA                    API (JSON)                     Trang Jinja goiso
   GET /            index.html     /api/auth/*   (đăng nhập chung) /b/<cn>/counter|display|cho
   GET /<path>      SPA fallback   /api/employees|units|...        /dat-lich  /lich-hen/<token>
   /assets/*        static         /api/goiso/*  (mới)            /admin      (+ /api/admin/*)
                                   /api/b/*, /api/booking/*,       templates + /static/*
                                   /api/ping, /api/kiosk/*  (tương thích kiosk, X-Branch-Key)
```

## Backend — `app/`

| Gói | Vai trò |
|---|---|
| `app/__init__.py` | App factory: extensions, JWT (header + cookie), error handlers, `_register_spa` (phục vụ `frontend/dist`) |
| `app/modules/auth/` | Đăng nhập CHUNG — JWT access/refresh, phát kèm cookie để trang Jinja dùng SSO |
| `app/modules/nhansu/` | `employees, units, positions, roles, users, audit` (blueprint) |
| `app/modules/goiso/` | `legacy_app` (49 route cũ, blueprint tương thích) + `queue_logic`/`booking_logic`/`tts` + `legacy_db` (shim SQLAlchemy) + `identity` (map user platform → user goiso) |
| `app/models/` | SQLAlchemy: user/rbac/organization/position/employee/audit/token |
| `app/services/`, `app/repositories/` | Nghiệp vụ nhân sự (chức vụ đơn nhất, transfer, scope…) |
| `app/permissions/` | Danh mục quyền + phân giải phạm vi đơn vị |
| `app/common/` | Response chuẩn `{success,message,data,errors}`, exceptions, auth_context |
| `migrations/` | Alembic — schema toàn platform (0001→0006) |
| `scripts/` | `create_admin`, `seed`, `migrate_goiso`, `migrate_goiso_users`, `link_goiso_units` |

## Xác thực

- **User**: JWT. SPA gửi `Authorization: Bearer` (token ở localStorage); trang Jinja
  goiso đọc cookie `access_token_cookie` (cùng phát khi đăng nhập). Một tài khoản,
  một lần đăng nhập, dùng cả hai module.
- **Thiết bị kiosk**: `X-Branch-Key` (khoá riêng mỗi chi nhánh) — không đổi.
- Phân quyền: `@require_permission` (nhân sự) / `admin_required` + `counter_guard`
  (goiso). Xem `docs/PERMISSIONS.md`.

## Dữ liệu

Một CSDL MySQL. Bảng `goiso_*` cạnh bảng nhân sự; `organization_units.goiso_branch_code`
nối cây đơn vị dùng chung với chi nhánh gọi số. Xem `docs/DATABASE.md`.

## Realtime

SSE `GET /api/b/<cn>/stream` — hub in-process (`_subscribers` theo branch_id).
Waitress chạy `--threads=48` để đủ kết nối giữ mở (mỗi TV/bảng chờ = 1 kết nối).

## Nguyên tắc giữ trong quá trình hợp nhất

ổn định > refactor đẹp · tương thích > đổi API · migration an toàn > làm nhanh ·
module hoá > trộn code · backend authorization > chỉ ẩn UI.
