# MERGE_ANALYSIS — Hợp nhất `goiso_kios` + `qlns_vpdk` thành một platform

> Phase 1 (ANALYZE). Tài liệu này chỉ phân tích, **chưa sửa code**.
> Ngày lập: 2026-09-10.

---

## 0. Nguồn đã đọc

| Hệ thống | Vị trí source | Vị trí đang chạy |
|---|---|---|
| Gọi số / kiosk (`goiso`) | `D:\QUANGTUAN\goiso_kios` | waitress `127.0.0.1:5050` (hiện **không** chạy) + Cloudflare Tunnel |
| Quản lý nhân sự (`nhansu`) | `D:\DEPLOY\qlns_vpdk` (đã đọc toàn bộ `backend/app`, `frontend/src`) | waitress `127.0.0.1:5000` + `QLNS_Nginx` :8080 + Cloudflare Tunnel |

Cloudflare Tunnel chạy bằng **service `Cloudflared`** với `--token-file` → cấu hình ingress (hostname → service) nằm trên **dashboard Cloudflare Zero Trust**, không có file local. Việc đổi tên miền / thêm subdomain phải làm trên dashboard đó.

---

## 1. Kiến trúc hiện tại — đối chiếu

| Khía cạnh | `goiso` | `nhansu` |
|---|---|---|
| Khung Flask | 1 file `server/app.py` (934 dòng), **không** blueprint | App-factory `create_app()` + **7 blueprint** theo module |
| ORM | **Không** — `sqlite3` thuần, `server/db.py` (717 dòng) | SQLAlchemy 2.x + Flask-Migrate (Alembic, 4 revision) |
| CSDL | SQLite `hethong_v2.db` (WAL). 24 chi nhánh, queue realtime, 12 user | MySQL 8 `personnel_management`, 16 bảng, **742 nhân sự**, 1 user |
| Xác thực | Session cookie (`session["uid"]`), mật khẩu **sha256** | **JWT** access/refresh, mật khẩu **Argon2**, refresh-token revoke qua bảng `refresh_tokens` |
| Phân quyền | 2 mức cứng: `role='admin'` hoặc `role='staff'` (buộc 1 chi nhánh) | RBAC đầy đủ: `roles / permissions / user_roles / role_permissions`; decorator `@require_permission("...")`; **scope theo cây đơn vị** (`user_unit_scopes`: GLOBAL/UNIT/SUBTREE) |
| Đơn vị / chi nhánh | Bảng `branches` (`id, code, full_name, api_key, display_token, active, display_order`) — phẳng | Bảng `organization_units` — **cây** (`parent_id, unit_type, sort_index`), nhiều cấp HEAD_OFFICE/DEPARTMENT/BRANCH/SECTION |
| Chuẩn response | `jsonify(error=...)` / dict thô, **không** chuẩn | `{ success, message, data, errors }` (`app/common/responses.py`) |
| Xử lý lỗi | 1 handler cho `sqlite3.OperationalError` | Global error handlers (`app/errors.py`), không lộ stack trace |
| Realtime | **SSE hub in-process** (`_subscribers: branch_id -> set[Queue]`), waitress `--threads=32` | Không |
| Frontend | **Server-rendered Jinja** — 11 template (`admin, counter, display, board, booking, login, index...`) + vanilla JS + SSE | **React 18 + Vite SPA** — react-router, @tanstack/react-query, axios (interceptor auto-refresh), TailwindCSS, tokens.css |
| Nền tảng khách kèm theo | **Kiosk desktop** (CustomTkinter) + **Inno Setup installer** (`installer/GoSoKiosk.iss`) + auto-update qua `/api/kiosk/version` & `/api/b/<code>/heartbeat` (xác thực bằng `X-Branch-Key`) | Không |
| Nghiệp vụ chính | `queue_logic.py` (cấp/gọi/recall/miss/done, khoá giờ, giới hạn ngày), `booking_logic.py` (đặt lịch online + Turnstile), `tts.py` (edge-tts) | `services/` (assignment, employee, unit, position, role, user, auth, audit, org_index); quy tắc **chức vụ đơn nhất** (`unit_position_limits.max_holders`) |
| Cấu hình bí mật | `GOISO_SECRET`, `GOISO_BASE_URL`, `TURNSTILE_*` qua env; `run_server.bat` **hard-code** `GOISO_BASE_URL=https://goiso.kh2959bmt.xyz` + secret | `.env` (backend) — `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `CORS_ORIGINS=...,https://nhansu.kh2959bmt.xyz` |

**Kết luận:** hai hệ khác nhau gần như mọi tầng. `nhansu` có kiến trúc tốt hơn hẳn (factory, blueprint, RBAC, migration, response chuẩn) → **lấy `nhansu` làm khung**, đưa `goiso` vào làm module, giữ nguyên hành vi đối ngoại của `goiso`.

---

## 2. Điểm trùng & xung đột

### 2.1 Trùng khái niệm
- **Chi nhánh / đơn vị**: `goiso.branches` vs `nhansu.organization_units`. Cùng phục vụ **Văn phòng Đăng ký đất đai** (Đắk Lắk + Phú Yên). goiso có 24 chi nhánh khu vực (`eakar, bmt, tuyhoa, dongxuan...`). → Dùng **một** bảng đơn vị (`organization_units`); goiso tham chiếu tới nó. Nhưng `branches` mang thêm `api_key`, `display_token`, `display_order` mà kiosk cần → cần bảng phụ mở rộng, **không xoá dữ liệu branches**.
- **User / auth**: cả hai đều có bảng `users` + khái niệm "admin". → Gộp về **một** bảng `users` (bản `nhansu`), migrate 12 user goiso sang, cấp role `GOISO_*`.
- **Admin**: cả hai đều phục vụ `/admin` và `/api/admin/*`. → **Xung đột đường dẫn** (xem 2.2).

### 2.2 Xung đột đường dẫn API (QUAN TRỌNG — kiosk đã phát hành phụ thuộc)
Đường dẫn goiso hiện tại **không** có tiền tố `/api/goiso`:

| Nhóm | Đường dẫn hiện tại | Ai gọi |
|---|---|---|
| Cấp số / trạng thái | `POST /api/b/<code>/ticket`, `GET /api/b/<code>/state`, `/api/b/<code>/stream` (SSE), `/api/b/<code>/tts`, `/api/b/<code>/checkin`, `/api/b/<code>/config/public` | Kiosk desktop, màn hình display, board |
| Quầy | `POST /api/b/<code>/counter/<id>/{next,recall,done,missed,call,status,login}` | Trang `counter.html` (nhân viên) |
| Thiết bị | `GET /api/ping`, `GET /api/branches`, `GET /api/kiosk/version`, `POST /api/b/<code>/heartbeat` | **Kiosk đã cài + Configurator** — không đổi được |
| Admin goiso | `GET/POST /api/admin/{users,branches,stats,devices,kiosk-release}`, `/api/admin/b/<code>/config`, `/api/admin/b/<code>/appointments`, `/api/admin/b/<code>/reset-today` | Trang `admin.html` |
| Đặt lịch | `/api/booking/branches`, `/api/booking/<code>/slots`, `/api/booking/<code>/book`, `/api/booking/appt/<token>[/cancel]` | Trang `booking.html` công khai |
| Auth goiso | `POST /api/login`, `POST /api/logout`, `GET /api/me` | Trang `login.html` |
| Trang HTML | `/`, `/b/<code>/{counter,display,display/simple,cho,man-hinh}`, `/admin`, `/login`, `/dat-lich`, `/lich-hen/<token>` | Trình duyệt / TV / kiosk |

→ `POST /api/login`, `GET /api/me`, `/api/admin/*` **đụng** với ý muốn của spec (`/api/auth/*`, `/api/admin/*` dùng chung).
**Giải pháp:** compatibility layer — giữ nguyên toàn bộ đường dẫn goiso cũ (mount blueprint ở prefix cũ), route MỚI cho platform đặt ở namespace riêng:
- Auth chung: `/api/auth/*` (đã có ở nhansu). `/api/login` cũ của goiso → **redirect 308** sang `/api/auth/login` sau khi lớp cookie SSO xong (Phase 5); trước đó giữ nguyên.
- Admin: quản trị goiso đổi thành `/api/goiso/admin/*` (mới) **và** giữ `/api/admin/*` cũ trỏ cùng handler tới hết Phase 7; "admin chung" của platform (quản lý user/role toàn hệ) dùng blueprint `roles`/`users` sẵn có của nhansu (`/api/users`, `/api/roles`) — **không** cần `/api/admin/*` mới.

### 2.3 Xung đột kỹ thuật
| # | Vấn đề | Ảnh hưởng | Hướng xử lý |
|---|---|---|---|
| C1 | Session (goiso) vs JWT (nhansu) | Không thể có 2 cơ chế đăng nhập | JWT làm chuẩn. Trang Jinja goiso đọc JWT từ **cookie HttpOnly** (`access_token`, `domain=COOKIE_DOMAIN`) do `/api/auth/login` phát kèm. API vẫn `Authorization: Bearer`. |
| C2 | Kiosk dùng `X-Branch-Key` (không phải user) | Đây là *device principal*, khác *user principal* | Giữ nguyên `require_branch_key`. Auth có 2 loại: user (JWT) + device (branch key). **Không gộp.** |
| C3 | `admin_required` check `role=='admin'` chuỗi cứng | Sau khi gộp user không còn cột `role` phẳng | Thay bằng `@require_permission("GOISO_ADMIN")`; `SYSTEM_ADMIN` có toàn quyền. |
| C4 | Response shape khác nhau | Frontend Jinja + kiosk parse `{error: ...}` / dict thô | **Không đổi** response của endpoint goiso cũ. Chỉ áp `{success,data,message}` cho endpoint mới `/api/goiso/*`. |
| C5 | SSE giữ kết nối + waitress threads | 1 tiến trình chung phải đủ thread cho SSE (mỗi TV/among/board = 1 connection dài) | waitress `--threads=48` (hoặc tách SSE sang chạy nền). Kiểm thử tải trước khi chốt. |
| C6 | goiso không có migration; nhansu dùng Alembic | Schema goiso phải vào Alembic sau khi lên MySQL | Phase 6: tạo revision `goiso_*`; script import SQLite→MySQL có log. |
| C7 | 2 frontend khác hệ (Jinja vs React) | Yêu cầu "dùng giao diện như quản lý nhân sự" | Portal + quản trị goiso → **build lại trong React SPA**. Kiosk/display/board/counter/booking (full-screen công khai) → **giữ Jinja** (spec mục 12 cho phép). |
| C8 | Token lưu ở `localStorage` (nhansu `tokenStore`) — không chia sẻ subdomain | SSO qua `goiso.<domain>` + `nhansu.<domain>` không tự có | Khuyến nghị **1 origin duy nhất theo path** (`/`, `/goiso`, `/nhansu`) thay vì SSO nhiều subdomain; nếu vẫn cần subdomain → chuyển sang cookie `domain=.<domain>`. |
| C9 | `SEND_FILE_MAX_AGE_DEFAULT=0` (goiso) vs cache mặc định (nhansu) | Cấu hình app khác nhau | Giữ theo blueprint: static goiso set header riêng. |
| C10 | `branches.code` (mã ngắn) là khoá kiosk dùng ở URL `/b/<code>/...` | Không thể đổi code → `organization_units.code` có thể khác | Bảng phụ `goiso_branch_ext.slug` giữ đúng `code` cũ; URL vẫn `/b/<slug>/`. |

---

## 3. Phụ thuộc

**goiso** (`server/requirements.txt`): `Flask>=3.0`, `waitress>=3.0`, `edge-tts>=7.0`. Ngoài ra dùng stdlib (`sqlite3, threading, queue, hashlib`). Kiosk desktop: `customtkinter`, `pillow`, `requests`, `pywin32` (in vé) — **tách riêng, không đụng backend**.

**nhansu** (`backend/requirements.txt`): Flask 3.0.3, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-Cors, **SQLAlchemy 2.0.52** (đã vá cho Python 3.14 — bản pin 2.0.32 trong file lỗi), PyMySQL, argon2-cffi, marshmallow, openpyxl, gunicorn (+ waitress cài thủ công).

Frontend nhansu: React 18, Vite 5, react-router-dom 6, @tanstack/react-query 5, axios, tailwindcss 3, clsx, vitest.

→ Requirements hợp nhất = union của hai (thêm `edge-tts`, `waitress` vào `requirements.txt` chuẩn).

---

## 4. Rủi ro

| Mức | Rủi ro | Giảm thiểu |
|---|---|---|
| 🔴 Cao | Migrate CSDL sống (742 nhân sự MySQL + queue realtime 24 chi nhánh SQLite). Spec muốn Postgres. | **Giữ MySQL** (nhansu đã ổn định ở đó). goiso: giữ SQLite chạy tạm ở Phase 3, chuyển sang `goiso_*` trên **cùng MySQL** ở Phase 6 bằng script có log, verify rồi mới bỏ SQLite. Không đụng Postgres (mục 25: "ổn định > refactor đẹp"). |
| 🔴 Cao | Kiosk đã phát hành + installer gọi đường dẫn cũ; đổi API = chết kiosk ngoài hiện trường | Compatibility layer bắt buộc; giữ `X-Branch-Key`; giữ `/api/ping`, `/api/kiosk/version`, `/api/b/<code>/heartbeat` **nguyên trạng**. Test bằng kiosk thật trước khi cắt. |
| 🟠 Vừa | SSE trong 1 tiến trình chung — cạn thread → treo cả nhân sự | Tăng threads + kiểm thử; theo dõi; phương án B: chạy SSE ở cổng phụ nội bộ. |
| 🟠 Vừa | Đổi tên miền: CORS, `COOKIE_DOMAIN`, Turnstile site key (theo domain), Cloudflare ingress | Tập trung vào `.env` (`APP_DOMAIN`, `COOKIE_DOMAIN`), không hard-code; cập nhật dashboard Cloudflare + Turnstile key khi cắt domain. |
| 🟠 Vừa | Gộp user: 12 user goiso (`cnbmt.*`) và 1 user nhansu (`admin`) — trùng username `admin` | Migrate script: `admin` goiso hợp nhất vào `admin` nhansu (giữ hash Argon2 của nhansu); user `cnbmt.*` tạo mới + role `GOISO_COUNTER` + scope UNIT = chi nhánh tương ứng. Mật khẩu sha256 cũ không dùng lại được với Argon2 → buộc đặt lại hoặc giữ cột `legacy_sha256` để verify-then-rehash lần đăng nhập đầu. |
| 🟡 Thấp | Chức năng "reset-today", "delete branch" của goiso xoá cứng dữ liệu | Giữ nguyên hành vi; thêm audit log. |
| 🟡 Thấp | 2 bộ font/asset trùng | Dọn ở Phase 7. |

---

## 5. Kiến trúc đề xuất (chốt)

### 5.1 Nguyên tắc
- **Repo/thư mục mới** `platform/` (đề xuất `D:\QUANGTUAN\platform`). Hai repo cũ **giữ nguyên** làm nguồn + fallback tới khi platform chạy thật ổn.
- Khung = backend `nhansu` (factory + blueprint + RBAC + migration + response chuẩn).
- goiso vào `app/modules/goiso/` — **giữ hành vi đối ngoại 100%**, refactor nội bộ từng bước.
- 1 backend Flask, 1 waitress: `waitress-serve --host=0.0.0.0 --port=5050 wsgi:app`.
- Một DB (MySQL). Một bảng `users`. Một bảng đơn vị (`organization_units`).

### 5.2 Cây thư mục đích
```
platform/
├── wsgi.py                      # waitress entry: app = create_app()
├── app.py                       # dev entry: python app.py
├── config.py                    # gộp BaseConfig + GOISO_* + APP_DOMAIN/COOKIE_DOMAIN
├── requirements.txt             # union
├── .env.example
├── core/            (= app/ hiện tại của nhansu, đổi tên khối hạ tầng)
│   ├── extensions.py  database.py  security.py  permissions.py  decorators.py  logging.py
├── auth/                        # từ app/modules/auth + app/services/auth_service + schemas
│   ├── models.py  routes.py  services.py  schemas.py
├── modules/
│   ├── goiso/
│   │   ├── models.py            # P6: goiso_* SQLAlchemy (P3: import y nguyên db.py cũ)
│   │   ├── routes.py            # /api/goiso/*   (mới, response chuẩn)
│   │   ├── routes_compat.py     # /api/b, /api/booking, /api/ping, /api/kiosk, /api/admin (cũ, nguyên trạng)
│   │   ├── pages.py             # /b/<code>/..., /dat-lich, /admin/goiso  (Jinja)
│   │   ├── services.py          # = queue_logic.py + booking_logic.py
│   │   ├── repositories.py      # P6
│   │   ├── tts.py  utils.py
│   └── nhansu/                  # = app/modules/{employees,units,positions,roles,users,audit} gom lại
│       ├── models.py routes.py services.py repositories.py schemas.py utils.py
├── admin/                       # mỏng: dashboard tổng hợp; phần lớn dùng lại users/roles blueprint
├── shared/
│   ├── constants.py  helpers.py  responses.py   (= app/common/*)
├── templates/    (11 template goiso)   static/   (js/css goiso + build React)
├── migrations/   (Alembic — thêm revision goiso_* ở P6)
├── frontend/     (React SPA nhansu, thêm route /goiso/*)
├── tests/        scripts/  (create_admin, seed, migrate_goiso.py, migrate_nhansu.py)
└── docs/         (ARCHITECTURE, DEPLOYMENT, DATABASE, PERMISSIONS, MIGRATION)
```
> Không bắt buộc khớp 100% mẫu trong đề bài — ưu tiên giữ blueprint sẵn có của nhansu đang tốt.

### 5.3 Blueprint & URL
```python
app.register_blueprint(auth_bp,        url_prefix="/api/auth")     # có sẵn
app.register_blueprint(nhansu_*_bp)                                # /api/employees, /api/units, ... giữ nguyên
app.register_blueprint(goiso_bp,       url_prefix="/api/goiso")    # MỚI, response chuẩn
app.register_blueprint(goiso_compat_bp)                            # /api/b, /api/booking, /api/ping, /api/kiosk, /api/admin  (NGUYÊN TRẠNG)
app.register_blueprint(goiso_pages_bp)                             # /, /b/<code>/*, /dat-lich, /admin/goiso  (Jinja)
```
Không đổi tên API hàng loạt. Mọi thay đổi đường dẫn cũ → 308 redirect.

### 5.4 CSDL đích (MySQL, prefix rõ ràng)
- **Giữ nguyên**: `users, roles, permissions, user_roles, role_permissions, user_unit_scopes, refresh_tokens, organization_units, positions, unit_position_limits, employees, employee_assignments, employee_education, job_grades, audit_logs`.
- **Thêm permission** (bảng `permissions`): `GOISO_VIEW, GOISO_COUNTER, GOISO_ADMIN` (+ giữ nhóm `employee.*`, `unit.*`... hiện có; bổ sung `NHANSU_*` alias nếu muốn theo đúng đề — nhưng không bắt buộc, permission hiện tại đã mịn hơn).
- **Bảng mới (Phase 6, từ SQLite)**: `goiso_branch_ext(unit_id PK/FK, slug UNIQUE, api_key, display_token, display_order, active)`, `goiso_queue`, `goiso_counters_status`, `goiso_config`, `goiso_visitor_stats`, `goiso_appointments`, `goiso_devices` — mọi `branch_id` → **FK `organization_units.id`**.
- **Tích hợp (Phase 7+)**: `goiso_counter_assignments(unit_id, counter_id, employee_id FK employees.id, branch_id)` — biết cán bộ nào trực quầy nào (mục 10); không lưu tên dạng text.
- **Chức vụ đơn nhất** (mục 8) — đã có `unit_position_limits.max_holders`. Bổ sung: partial-unique index không khả thi ở MySQL; thay bằng **kiểm tra trong transaction** ở `assignment_service` (đã có một phần) + test hồi quy.

### 5.5 Auth / SSO
- `/api/auth/login` phát JWT như hiện tại **và** set cookie `access_token` (HttpOnly, SameSite=Lax, `domain` = `COOKIE_DOMAIN` nếu đặt, path=/). Trang Jinja goiso đọc cookie này qua `verify_jwt_in_request(locations=["cookies","headers"])`.
- Bỏ `session["uid"]` của goiso; `/api/login`, `/api/logout`, `/api/me` cũ → chuyển tiếp sang `/api/auth/*` (giữ đường cũ 1 thời gian, trả cùng payload tối thiểu mà `login.html` cần).
- Kiosk device: `X-Branch-Key` **không đổi**.
- Quyền:
  - `SYSTEM_ADMIN` → toàn quyền (đã vậy).
  - `GOISO_ADMIN` → `/admin/goiso`, `/api/goiso/admin/*`, `/api/admin/*` (compat).
  - `GOISO_COUNTER` → `/b/<code>/counter` + `/api/b/<code>/counter/*`, chỉ chi nhánh trong `user_unit_scopes`.
  - `GOISO_VIEW` → display/board/stats chỉ đọc.
- Portal chỉ hiện module user có quyền (`GOISO_*` → thẻ "Bốc số – Gọi số"; `employee.view` → thẻ "Quản lý nhân sự"; `SYSTEM_ADMIN`/`role.view` → "Quản trị hệ thống").

### 5.6 Triển khai
- 1 tiến trình: `waitress-serve --host=0.0.0.0 --port=5050 --threads=48 wsgi:app` (NSSM service `PLATFORM_Backend`).
- Static React: `QLNS_Nginx` (đổi tên `PLATFORM_Nginx`) serve `frontend/dist`, proxy `/api`, `/b`, `/admin`, `/dat-lich`, `/lich-hen`, `/static` → `127.0.0.1:5050`. (Hoặc để Flask serve hết — quyết định ở P8.)
- Cloudflare Tunnel: trỏ mọi hostname domain mới → `http://127.0.0.1:8080` (nginx) hoặc `:5050`. Cấu hình trên dashboard.
- `.env` (không commit): `APP_DOMAIN=`, `COOKIE_DOMAIN=`, `DATABASE_URL=`, `SECRET_KEY=`, `JWT_SECRET_KEY=`, `CORS_ORIGINS=`, `GOISO_SECRET=` (bỏ — dùng chung `SECRET_KEY`), `TURNSTILE_SITE_KEY=`, `TURNSTILE_SECRET=`, `TTS_*`.
- Gỡ hard-code trong `run_server.bat` (secret + domain) → đọc từ `.env`.

---

## 6. Kế hoạch phase (bám mục 22, test + commit sau mỗi phase)

| Phase | Nội dung | Tiêu chí xong |
|---|---|---|
| **P1** ✅ | Tài liệu này | Đã có `docs/MERGE_ANALYSIS.md` |
| **P2** | Tạo `platform/`, copy khung `nhansu` (backend factory + core + auth + frontend), chạy cổng 5050, kết nối MySQL hiện có | Nhân sự chạy **nguyên trạng** trên cấu trúc mới; `pytest` xanh; login + list employees OK |
| **P3** | Đưa `goiso` vào `modules/goiso` giữ `db.py` SQLite tạm; mount compat routes + pages + templates | Kiosk cấp số / gọi số / done / recall / booking / heartbeat / SSE chạy lại; test nghiệp vụ queue xanh |
| **P4** | Chuẩn hoá module nhân sự trong cấu trúc mới + bổ sung test business (chức vụ đơn nhất, transfer, scope) | Test P4 xanh; API nhân sự không đổi |
| **P5** | Auth gộp: migrate 12 user goiso → `users`; permission `GOISO_*`; decorator; cookie SSO cho Jinja; redirect `/api/login`→`/api/auth/login` | 1 tài khoản đăng nhập dùng được cả 2 module; kiosk `X-Branch-Key` vẫn chạy |
| **P6** | Đơn vị dùng chung: map `branches`↔`organization_units` (+`goiso_branch_ext`); chuyển bảng goiso sang `goiso_*` MySQL; `scripts/migrate_goiso.py` (log nguồn/đích/lỗi/bỏ qua); giữ SQLite tới khi verify | Số liệu khớp 100%; SQLite chỉ còn để backup |
| **P7** | Portal React (chọn ứng dụng theo quyền) + màn quản trị goiso trong SPA (chi nhánh, dịch vụ, quầy, màn hình, thống kê, thiết bị, đặt lịch) | Giao diện đồng nhất kiểu nhân sự; kiosk công khai vẫn Jinja |
| **P8** | Triển khai: waitress 1 tiến trình, NSSM, nginx, Cloudflare Tunnel domain mới, `.env`, `README` + `docs/*` | Chạy thật domain mới; rollback plan sẵn sàng |

Mỗi phase = 1 commit riêng (`refactor: create shared platform foundation`, `feat: migrate goiso into module architecture`, ...).

---

## 7. Việc KHÔNG làm (theo mục 21)
Không rewrite; không phá kiosk/installer; không đổi tên API hàng loạt; không xoá SQLite trước khi migrate xong & verify; không hard-code domain/secret; không tạo 2 bảng chi nhánh; không tạo 2 bảng user; không login riêng từng module; **không** chuyển sang PostgreSQL (giữ MySQL cho an toàn — nếu sau này bắt buộc Postgres thì làm thành dự án migration riêng).

---

## 8. Câu hỏi cần chốt trước khi sang P2 (không suy ra được từ code)
1. **Tên miền mới** là gì? (dùng cho `APP_DOMAIN`, `COOKIE_DOMAIN`, `CORS_ORIGINS`, Turnstile, Cloudflare ingress).
2. Mô hình truy cập: **một domain theo path** (`/`, `/goiso`, `/nhansu` — đơn giản, SSO tự nhiên) hay **subdomain** (`goiso.`, `nhansu.`, `admin.` — cần cookie `.<domain>`)? (đề xuất: một domain theo path).
3. Xác nhận **giữ MySQL** (không Postgres) cho bản hợp nhất.
4. Thư mục platform: `D:\QUANGTUAN\platform` (mới) — đồng ý?
