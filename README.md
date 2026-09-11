# Platform — Hệ thống hợp nhất Gọi số (goiso) + Quản lý nhân sự

Hai hệ thống gộp thành **một backend Flask (API thuần JSON) + một Portal React (SPA)**,
chạy trên **một tiến trình Waitress**. Không còn Jinja/template phía server — toàn bộ
giao diện (portal, nhân sự, quản trị, bàn gọi số, màn hình TV, bảng chờ, đặt lịch) đều
là route React.

```
Platform  (waitress :5000  ->  wsgi:app)
├── /                                  Portal React — chọn ứng dụng theo quyền
├── /nhan-su, /employees…              SPA Quản lý nhân sự
├── /admin/*                           SPA Quản trị (tài khoản, vai trò, nhật ký, gọi số)
├── /b/<cn>/counter|display|cho|man-hinh, /dat-lich, /lich-hen/<token>, /cho
│                                       SPA Gọi số (kiosk/TV/bảng chờ/đặt lịch)
├── /api/auth/*                        Đăng nhập CHUNG (JWT — Bearer + cookie)
├── /api/employees|units|positions|users|roles|audit-logs   Module Nhân sự
├── /api/admin/*                       Quản trị gọi số (chi nhánh, dịch vụ, quầy, thống kê...)
└── /api/b/*, /api/booking/*, /api/ping, /api/kiosk/*        API gọi số + tương thích kiosk vật lý (X-Branch-Key)
```

## Tài liệu

| | |
|---|---|
| [docs/MERGE_ANALYSIS.md](docs/MERGE_ANALYSIS.md) | Phân tích 2 hệ cũ + kiến trúc chốt + kế hoạch 8 phase |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Sơ đồ + vai trò từng gói |
| [docs/DATABASE.md](docs/DATABASE.md) | Một CSDL MySQL, bảng `goiso_*`, migration |
| [docs/PERMISSIONS.md](docs/PERMISSIONS.md) | Quyền & vai trò; ai vào được trang gọi số |
| [docs/MIGRATION.md](docs/MIGRATION.md) | Nạp dữ liệu hệ cũ (script có log) |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Triển khai + cắt chuyển tên miền + rollback |

## Trạng thái theo phase

| Phase | Nội dung | Trạng thái |
|---|---|---|
| P1 | Phân tích 2 codebase, chốt kiến trúc | ✅ |
| P2 | Dựng khung platform từ backend nhân sự | ✅ |
| P3 | Đưa goiso vào `modules/goiso` + lớp tương thích | ✅ |
| P4 | Gom module nhân sự vào `modules/nhansu` + test nghiệp vụ | ✅ |
| P5 | Đăng nhập chung (JWT + cookie SSO), quyền `GOISO_*`, vai trò `GOISO_COUNTER`, di trú tài khoản | ✅ |
| P6 | Gộp CSDL: bảng `goiso_*` + đơn vị dùng chung, script di trú có log | ✅ |
| P7 | Portal React theo quyền; một cổng phục vụ SPA + API | ✅ |
| P8 | Script + tài liệu triển khai, runbook cắt chuyển | ✅ (chờ tên miền + thao tác Cloudflare) |
| P9 | Bỏ hẳn Jinja: bàn gọi số/màn hình TV/bảng chờ/đặt lịch chuyển sang React (`frontend/src/pages/goiso/`); backend chỉ còn API JSON | ✅ |

## Chạy — development

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env    # sửa DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY
.venv\Scripts\flask --app wsgi db upgrade
python app.py             # http://127.0.0.1:5050

cd ../frontend && npm ci && npm run build   # -> frontend/dist (backend tự phục vụ)
```

## Chạy — production

```powershell
powershell -File scripts\deploy_platform.ps1 -Port 5050
# tương đương: waitress-serve --host=0.0.0.0 --port=5050 --threads=48 wsgi:app
```

## Kiểm thử

```bash
cd backend
set FLASK_ENV=testing && .venv\Scripts\pytest -q      # 43 test
```

## Lưu ý

- Hai hệ cũ giữ nguyên tại `D:\DEPLOY\qlns_vpdk` và `D:\QUANGTUAN\goiso_kios` làm nguồn + đường lùi cho tới khi platform chạy thật ổn.
- `backend/.env` **không** commit. CSDL thật (chứa CCCD) không lên git.
- Runtime dùng một CSDL MySQL (bảng `goiso_*` cùng chỗ với bảng nhân sự). Test chạy SQLite in-memory.
