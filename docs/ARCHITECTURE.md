# ARCHITECTURE — Platform hợp nhất

```
                         Cloudflare Tunnel (1 hostname / hoặc nhiều -> cùng đích)
                                        │
                              waitress  :5000  (một tiến trình)
                                        │  wsgi:app  = create_app()
        ┌───────────────────────────────┴───────────────────────────────┐
        │                                                               │
   Portal + SPA (React)                                            API (JSON, không session/Jinja)
   GET /            index.html (mọi route SPA đều trả file này)    /api/auth/*    đăng nhập chung
   GET /<path>      SPA fallback — React Router xử lý điều hướng   /api/employees|units|positions|users|roles|audit-logs
   /assets/*        JS/CSS đã build (Vite)                         /api/admin/*   quản trị gọi số
                                                                    /api/b/*, /api/booking/*, /api/ping, /api/kiosk/*
                                                                       (API gọi số + tương thích kiosk vật lý, X-Branch-Key)
```

Không còn Jinja/template phía server. Mọi trang — kể cả bàn gọi số, màn hình TV,
bảng chờ, đặt lịch online — là component React trong `frontend/src/pages/goiso/`,
gọi thẳng các API JSON trên bằng axios (cùng client, cùng cơ chế refresh token,
dùng cho cả nhân sự lẫn gọi số).

## Backend — `app/` (chỉ còn API)

| Gói | Vai trò |
|---|---|
| `app/__init__.py` | App factory: extensions, JWT (header + cookie), error handlers, `_register_spa` (phục vụ `frontend/dist`, mọi route không khớp API đều trả `index.html`) |
| `app/modules/auth/` | Đăng nhập CHUNG — JWT access/refresh, phát kèm cookie |
| `app/modules/nhansu/` | `employees, units, positions, roles, users, audit` (blueprint) |
| `app/modules/goiso/` | `legacy_app` (blueprint API — cấp số, quầy, đặt lịch, quản trị `/api/admin/*`) + `queue_logic`/`booking_logic`/`tts` + `legacy_db` (shim SQLAlchemy) + `identity` (map user platform → quyền goiso). Không còn `templates/`, không còn `static/` — xoá ở lần dọn Jinja. |
| `app/models/` | SQLAlchemy: user/rbac/organization/position/employee/audit/token |
| `app/services/`, `app/repositories/` | Nghiệp vụ nhân sự (chức vụ đơn nhất, transfer, scope…) |
| `app/permissions/` | Danh mục quyền + phân giải phạm vi đơn vị |
| `app/common/` | Response chuẩn `{success,message,data,errors}` (nhân sự); goiso trả thẳng JSON `{...}` / `{error:"..."}` — xem `frontend/src/lib/goisoApi.js`, `goisoQueueApi.js` |
| `migrations/` | Alembic — schema toàn platform (0001→0006) |
| `scripts/` | `create_admin`, `seed`, `migrate_goiso`, `migrate_goiso_users`, `link_goiso_units` |

## Frontend — `frontend/src/`

| Gói | Vai trò |
|---|---|
| `pages/` (`nhan-su`, `employees/`, `units/`, `positions/`) | Module Nhân sự — trong khung `components/Layout.jsx` (sidebar) |
| `pages/admin/` | Trang Quản trị DUY NHẤT (`/admin`, có tab) — tài khoản/vai trò/nhật ký + `pages/admin/goiso/*` (chi nhánh, cấu hình, thống kê, thiết bị) |
| `pages/goiso/` | Giao diện gọi số **toàn màn hình, không có sidebar**: `CounterPage` (bàn gọi số), `DisplayPage`/`DisplaySimplePage` (màn hình TV), `BoardPage` (bảng chờ công khai), `BookingPage`/`BookingLookupPage` (đặt lịch), `ScreensPickPage`, `BranchPickerPage` (`/cho`) |
| `lib/goisoVoice.js` | Đọc số tiếng Việt + chuông + TTS (port từ `common.js` cũ) |
| `lib/goisoStream.js` | Hook SSE `useGoisoStream(branchCode, onEvent)` |
| `lib/goisoQueueApi.js` | Client cho `/api/b/*`, `/api/booking/*`, `/api/ping`, `/api/branches` |
| `lib/goisoApi.js` | Client cho `/api/admin/*` (quản trị gọi số) |

## Xác thực

- **User**: JWT — SPA gửi `Authorization: Bearer` (token ở localStorage) cho MỌI
  request, kể cả gọi số (không còn phụ thuộc cookie vì không còn trang server-render).
  `/api/auth/login` vẫn phát kèm cookie (vô hại, dự phòng) nhưng không có gì phụ thuộc nó.
- **Thiết bị kiosk vật lý** (`kiosk/goso_kiosk.py`, app desktop riêng): `X-Branch-Key`
  (khoá riêng mỗi chi nhánh) — không đổi, không liên quan tới việc bỏ Jinja lần này.
- Phân quyền: `@require_permission` (nhân sự) / `admin_required` + `counter_guard`
  (goiso) — backend luôn kiểm tra, frontend chỉ ẩn nút. Xem `docs/PERMISSIONS.md`.

## Dữ liệu

Một CSDL MySQL. Bảng `goiso_*` cạnh bảng nhân sự; `organization_units.goiso_branch_code`
nối cây đơn vị dùng chung với chi nhánh gọi số. Xem `docs/DATABASE.md`.

## Realtime

SSE `GET /api/b/<cn>/stream` — hub in-process (`_subscribers` theo branch_id), React
kết nối qua `useGoisoStream`. Waitress chạy `--threads=48` để đủ kết nối giữ mở
(mỗi TV/bảng chờ = 1 kết nối).

## Nguyên tắc giữ trong quá trình hợp nhất

ổn định > refactor đẹp · tương thích > đổi API · migration an toàn > làm nhanh ·
module hoá > trộn code · backend authorization > chỉ ẩn UI.
