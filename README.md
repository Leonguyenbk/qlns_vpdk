# Hệ thống quản lý nhân sự – Giai đoạn 1

Ứng dụng web quản lý nhân sự: tài khoản & phân quyền (RBAC + phạm vi đơn vị), cơ cấu đơn vị,
chức vụ & giới hạn chức vụ, hồ sơ nhân sự, quá trình công tác, chuyển đơn vị và nhật ký thao tác.

- **Backend:** Python Flask, Flask-SQLAlchemy, Flask-Migrate/Alembic, JWT (access + refresh, thu hồi bằng `jti`), Argon2.
- **Database:** MySQL 8 (`utf8mb4`). Test chạy trên SQLite in-memory.
- **Frontend:** React + Vite, React Router, TanStack Query, Axios (interceptor tự refresh token), React Hook Form + Zod, Tailwind CSS (tông xanh dương), giao diện tiếng Việt.

---

## 1. Cây thư mục

```text
personnel-management/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Application Factory
│   │   ├── config.py             # Cấu hình theo môi trường (đọc từ biến môi trường)
│   │   ├── extensions.py         # db, migrate, jwt, cors
│   │   ├── errors.py             # Xử lý lỗi tập trung -> JSON envelope
│   │   ├── logging_config.py     # Logging + lọc dữ liệu nhạy cảm
│   │   ├── common/               # responses, exceptions, utils, auth_context (decorator quyền)
│   │   ├── models/               # SQLAlchemy 2.x: user, rbac, organization, position, employee, token, audit
│   │   ├── schemas/              # Marshmallow schema kiểm tra kiểu/hình dạng request API
│   │   ├── repositories/         # Truy vấn (employee, unit) – tách khỏi service
│   │   ├── services/             # Nghiệp vụ: auth, unit, position, assignment, employee, user, role, audit
│   │   ├── permissions/          # Hằng số permission/vai trò + giải quyết phạm vi đơn vị (scope)
│   │   └── modules/              # Blueprint theo module: auth, employees, units, positions, users, roles, audit
│   ├── migrations/               # Alembic: 0001 schema, 0002 seed vai trò/quyền
│   ├── scripts/                  # seed.py (dữ liệu mẫu), create_admin.py (tài khoản quản trị)
│   ├── tests/                    # pytest (33 test)
│   ├── requirements.txt
│   ├── wsgi.py                   # điểm vào Flask/gunicorn
│   ├── entrypoint.sh             # chờ DB -> migrate -> seed -> create-admin -> chạy app
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── lib/                  # api.js (axios + interceptor refresh), constants, format, tokenStore
│   │   ├── auth/                 # AuthContext (đăng nhập, quyền)
│   │   ├── components/           # Layout, Sidebar, ProtectedRoute, Can, ui/*
│   │   ├── hooks/                # TanStack Query hooks theo domain
│   │   ├── schemas/              # Zod schema cho form
│   │   ├── pages/                # 15 trang (xem mục 9)
│   │   └── __tests__/            # vitest (18 test)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile + nginx.conf
│   └── .env.example
├── docker-compose.yml
├── .env.example
└── README.md
```

## 2. Kiến trúc (tóm tắt)

- **Application Factory + Blueprint theo module.** Mỗi module có `routes.py` mỏng; Marshmallow kiểm tra request trong `schemas/`, nghiệp vụ nằm ở `services/`, truy vấn phức tạp ở `repositories/`.
- **Envelope phản hồi thống nhất:** `{ success, message, data, errors }`; danh sách có `data.items` + `data.pagination`.
- **RBAC + phạm vi đơn vị.** Quyền lưu ở bảng `roles/permissions/role_permissions/user_roles`; phạm vi ở `user_unit_scopes` (GLOBAL / UNIT / SUBTREE, nhiều bản ghi/ tài khoản). Mọi API nhân sự tự lọc theo phạm vi (`app/permissions/scope.py`).
- **Transaction cho thao tác nhiều bước.** Chuyển đơn vị và thay thế người giữ chức vụ chạy trong một transaction, dùng `SELECT ... FOR UPDATE` (`with_for_update`) để khóa bản ghi, rollback toàn bộ nếu lỗi; ghi audit log trước & sau.
- **Không dùng `db.create_all()`** – toàn bộ schema qua migration Alembic. Timezone UTC trong DB, frontend đổi sang giờ địa phương.
- **Bảo mật:** JWT access ngắn hạn + refresh có thu hồi (`jti`), Argon2, giới hạn đăng nhập sai + khóa tạm, CORS từ biến môi trường, không trả stack trace ở production, không ghi mật khẩu/token vào log hay audit.
- **Frontend:** Protected Route + component `<Can>` để ẩn/khóa nút theo quyền — **backend luôn kiểm tra lại quyền**, không tin frontend.

## 3. Danh sách bảng database

| Bảng | Mô tả |
|---|---|
| `organization_units` | Đơn vị dạng cây (`HEAD_OFFICE/DEPARTMENT/BRANCH/SECTION`), `parent_id`, `is_active` |
| `positions` | Chức vụ: `code`, `level`, `is_managerial`, `is_active` |
| `unit_position_limits` | Giới hạn số người giữ 1 chức vụ tại 1 đơn vị (unique `unit_id`+`position_id`; `max_holders` NULL = không giới hạn) |
| `employees` | Hồ sơ nhân sự; soft delete (`is_deleted`, `deleted_at`); trạng thái nhiều giá trị |
| `employee_assignments` | Lịch sử phân công/quá trình công tác; phân công chính hiệu lực có `end_date = NULL` |
| `users` | Tài khoản; `failed_login_count`, `locked_until`, `last_login_at` |
| `roles`, `permissions`, `role_permissions`, `user_roles` | RBAC |
| `user_unit_scopes` | Phạm vi đơn vị của tài khoản (`GLOBAL/UNIT/SUBTREE`) |
| `refresh_tokens` | Theo dõi refresh token theo `jti` để thu hồi |
| `audit_logs` | Nhật ký thao tác: `action`, `entity_type/id`, `old_values/new_values` (JSON), `ip_address`, `user_agent` |
| `alembic_version` | Phiên bản migration |

## 4. Danh sách API

Tiền tố: `/api`. Các API nghiệp vụ yêu cầu `Authorization: Bearer <access_token>` và kiểm tra permission/phạm vi phù hợp. `/auth/refresh` và `/auth/logout` nhận refresh token; `/auth/login` và `/health` không yêu cầu token.

**Auth**
```
POST /auth/login            POST /auth/refresh        POST /auth/logout
GET  /auth/me               PUT  /auth/change-password
GET  /health
```

**Employees**
```
GET  /employees             # phân trang, tìm kiếm (keyword: mã/tên/SĐT), lọc unit/position/status/employment_type, sort full_name|recruitment_date|updated_at
POST /employees             GET /employees/{id}       PUT /employees/{id}
DELETE /employees/{id}      # soft delete
POST /employees/{id}/restore
GET  /employees/{id}/assignments
POST /employees/{id}/transfer   # body: to_unit_id, to_position_id, effective_date, decision_number/date, note, replace_existing
GET  /employees/dashboard   # số liệu tổng quan (theo phạm vi)
```

**Organization units**
```
GET /units                  GET /units/tree           POST /units
GET /units/{id}             PUT /units/{id}            DELETE /units/{id}   # ngừng hoạt động nếu đã có dữ liệu
```

**Positions & giới hạn chức vụ**
```
GET /positions              POST /positions           PUT /positions/{id}   DELETE /positions/{id}
GET  /units/{unit_id}/position-limits
POST /units/{unit_id}/position-limits
PUT  /units/{unit_id}/position-limits/{id}
```

**Users & phân quyền**
```
GET /users                  POST /users               GET /users/{id}       PUT /users/{id}
POST /users/{id}/reset-password
POST /users/{id}/roles              # body: { role_ids: [] }
POST /users/{id}/unit-scopes        # body: { scopes: [{ scope_type, unit_id }] }
GET /roles                  POST /roles               PUT /roles/{id}       DELETE /roles/{id}
GET /permissions
GET /audit-logs             # lọc action / entity_type / entity_id / user_id, phân trang
```

Mã HTTP: `200/201` thành công, `400` vi phạm nghiệp vụ, `401` chưa xác thực, `403` thiếu quyền/ngoài phạm vi, `404` không tìm thấy, `409` xung đột (mã trùng, giới hạn chức vụ – kèm `data` mô tả người đang giữ), `422` sai định dạng dữ liệu, `500` lỗi hệ thống.

## 5. Tài khoản mẫu

Sau khi seed (`flask --app wsgi seed`) và tạo admin (`flask --app wsgi create-admin`):

| Tài khoản | Mật khẩu | Vai trò | Phạm vi |
|---|---|---|---|
| `admin` | Giá trị `ADMIN_PASSWORD` trong `.env` | Quản trị hệ thống | Toàn hệ thống |
| `hradmin` | `Password@123` | Quản trị nhân sự | Toàn hệ thống |
| `cn01manager` | `Password@123` | Quản lý đơn vị | Chi nhánh 01 + cấp dưới |
| `viewer` | `Password@123` | Người xem | Toàn hệ thống (chỉ xem) |

Tạo admin thủ công:
```bash
# đặt ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL / ADMIN_FULL_NAME trong backend/.env
flask --app wsgi create-admin
```

Nếu tài khoản đã tồn tại và cần đặt lại mật khẩu theo `ADMIN_PASSWORD`, tạm đặt
`ADMIN_RESET_PASSWORD=true`, chạy lại `create-admin`, sau đó đổi về `false` để tránh
việc mật khẩu bị đặt lại ngoài ý muốn ở lần khởi động sau.

---

## 6. Chạy bằng Docker Compose

Yêu cầu: Docker Desktop.

```bash
cd personnel-management
cp .env.example .env            # bắt buộc đổi toàn bộ mật khẩu/secret mẫu
docker compose up --build
```

- Frontend: <http://localhost:8080>
- Backend API: <http://localhost:5000/api> · health: <http://localhost:5000/api/health>
- MySQL: `localhost:3306`

Container `backend` tự động: chờ MySQL healthy → `flask db upgrade` → seed dữ liệu mẫu (khi `SEED_ON_START=true`) → tạo tài khoản admin. Có `healthcheck` cho cả MySQL và backend.

Dừng: `docker compose down` (giữ dữ liệu) · `docker compose down -v` (xóa dữ liệu).

---

## 7. Chạy thủ công trên Windows (terminal VS Code / PowerShell)

### 7.1. Chuẩn bị MySQL 8

Tạo database và user (đảm bảo `utf8mb4`):
```sql
CREATE DATABASE personnel_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hr_user'@'%' IDENTIFIED BY 'your-strong-database-password';
GRANT ALL PRIVILEGES ON personnel_management.* TO 'hr_user'@'%';
FLUSH PRIVILEGES;
```

### 7.2. Backend

```powershell
cd personnel-management\backend

# Tạo môi trường Python
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài thư viện backend
python -m pip install --upgrade pip
pip install -r requirements.txt

# Cấu hình
copy .env.example .env
#  -> sửa DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY, CORS_ORIGINS trong .env

# Chạy migration (tạo bảng + seed vai trò/quyền)
flask --app wsgi db upgrade

# Seed dữ liệu mẫu (đơn vị, chức vụ, nhân sự, tài khoản mẫu)
flask --app wsgi seed

# Tạo tài khoản quản trị đầu tiên
flask --app wsgi create-admin

# Chạy backend (http://localhost:5000)
flask --app wsgi run
#  hoặc production: gunicorn "wsgi:app"   (Linux/Docker)
```

### 7.3. Frontend

```powershell
cd personnel-management\frontend

# Cài thư viện frontend
npm install

# Cấu hình URL API
copy .env.example .env
#  -> VITE_API_BASE_URL=http://localhost:5000/api

# Chạy frontend (http://localhost:5173)
npm run dev
```

### 7.4. Chạy test

```powershell
# Backend (SQLite in-memory, không cần MySQL)
cd personnel-management\backend
.\.venv\Scripts\Activate.ps1
$env:FLASK_ENV="testing"; pytest

# Frontend
cd personnel-management\frontend
npm test

# Build frontend production
npm run build
```

---

## 8. Kết quả kiểm thử (đã chạy)

**Migration**
```
INFO  [alembic] Running upgrade  -> 0001_initial_schema, Khởi tạo toàn bộ schema giai đoạn 1
INFO  [alembic] Running upgrade 0001_initial_schema -> 0002_seed_roles_permissions, Seed quyền và vai trò mẫu
$ flask --app wsgi db current
0002_seed_roles_permissions (head)
14 bảng + alembic_version · 17 permissions · 4 vai trò mẫu
```

**Seed**
```
33 đơn vị · 9 chức vụ · 63 cấu hình giới hạn chức vụ · 15 nhân sự
Tài khoản mẫu: hradmin, cn01manager, viewer
```

**Backend test**
```
$ pytest
33 passed
```
Bao phủ: đăng nhập đúng/sai, khóa sau nhiều lần sai, tài khoản khóa, từ chối khi thiếu token,
từ chối khi thiếu permission, lọc nhân sự theo phạm vi đơn vị, ẩn trường nhạy cảm, thêm/sửa
nhân sự, soft delete + khôi phục, chuyển đơn vị thành công (giữ lịch sử), rollback khi chuyển
lỗi, chặn chuyển vào đơn vị ngừng hoạt động, phát hiện & xác nhận thay thế chức vụ đạt giới hạn,
không cho 2 người cùng giữ chức vụ giới hạn 1, chống vòng lặp cây đơn vị, xóa đơn vị có dữ liệu
chỉ ngừng hoạt động; giới hạn chức vụ không thể đặt thấp hơn số người đang giữ; nhật ký được lọc theo phạm vi đơn vị; CRUD tài khoản/vai trò/phạm vi.

**Frontend test**
```
$ npx vitest run
Test Files  4 passed (4)
     Tests  18 passed (18)
```
Bao phủ: Protected Route (redirect login / 403 / cho qua), ẩn–hiện nút theo permission (`<Can>`),
kiểm tra dữ liệu form (Zod), xử lý lỗi API (message tiếng Việt, payload xung đột 409),
phân loại endpoint được phép tự refresh access token, form đăng nhập truyền đúng dữ liệu khi
gõ và nhấn Enter.

**Frontend build**
```
$ vite build
✓ 187 modules transformed
dist/index.html                    0.40 kB
dist/assets/index-*.css           22.24 kB │ gzip:  4.23 kB
dist/assets/index-*.js           424.87 kB │ gzip: 131.46 kB
✓ built in ~1.8s
```

---

## 9. Chức năng đã hoàn thành (Giai đoạn 1)

1. Đăng nhập / đăng xuất / refresh token / đổi mật khẩu / `me`; giới hạn đăng nhập sai + khóa tạm; thu hồi refresh token khi đổi mật khẩu hoặc khóa tài khoản.
2. Quản lý cơ cấu đơn vị dạng cây: thêm/sửa, ngừng hoạt động, xem cấp trên/cấp dưới, chống trùng mã, chống vòng lặp, không xóa cứng đơn vị có dữ liệu.
3. Quản lý chức vụ + `unit_position_limits` (giới hạn theo đơn vị); không cho hạ giới hạn thấp hơn số người đang giữ.
4. Hồ sơ nhân sự: CRUD, tìm kiếm, lọc, sắp xếp, phân trang từ backend; trường CCCD chỉ hiện với `employee.view_sensitive`.
5. Thêm/sửa/xóa (soft delete) và khôi phục nhân sự; danh sách có bộ lọc xem hồ sơ đã xóa và nút khôi phục theo quyền.
6. Chuyển đơn vị: form riêng, transaction, khóa bản ghi, phát hiện xung đột giới hạn chức vụ, xác nhận `replace_existing`, kết thúc phân công cũ, tạo phân công mới, giữ nguyên lịch sử, chặn đơn vị/chức vụ ngừng hoạt động, audit trước–sau, rollback khi lỗi.
7. Lịch sử công tác & lịch sử chuyển đơn vị (`employee_assignments`), trang xem lịch sử.
8. Phân quyền người dùng: vai trò, quyền, gán vai trò, gán phạm vi đơn vị (GLOBAL/UNIT/SUBTREE, nhiều phạm vi); bảo vệ vai trò/tài khoản Quản trị hệ thống.
9. Nhật ký thao tác cho toàn bộ hành động quan trọng; trang xem có lọc, phân trang và giới hạn theo phạm vi đơn vị.
10. Giao diện React: 15 trang — Đăng nhập, Dashboard, Danh sách/Thêm/Chi tiết/Sửa/Chuyển đơn vị/Lịch sử công tác nhân sự, Cơ cấu đơn vị, Chức vụ & giới hạn, Tài khoản, Vai trò & quyền, Nhật ký, 403, 404. Sidebar thu gọn, responsive, tông xanh dương, toast, modal xác nhận thay thế, menu ẩn theo quyền.

## 10. Cố ý để dành cho giai đoạn sau (Giao việc & KPI)

Chưa xây dựng và **không** tạo bảng/API/giao diện giả cho:

- Giao việc (assignment of tasks) và theo dõi tiến độ công việc.
- Đánh giá KPI.
- Thi đua, khen thưởng.
- Chấm công, tiền lương.

Đã chuẩn bị để mở rộng: mã nguồn tách theo module (`app/modules/<tên>`), lớp `services/` +
`repositories/` + `permissions/` dùng lại được; thêm module mới chỉ cần tạo blueprint + model +
migration + permission mới và khai báo trong `app/modules/__init__.py` và menu frontend
(`src/components/Layout.jsx`). Bảng `employee_assignments`, `audit_logs`, cơ chế RBAC + phạm vi
đơn vị đã sẵn sàng để các module Giao việc/KPI tham chiếu.
