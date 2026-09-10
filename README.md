# Platform — Hệ thống hợp nhất Gọi số (goiso) + Quản lý nhân sự

Hai hệ thống gộp thành **một backend Flask + một tiến trình Waitress**, module hoá rõ ràng.
Một cổng phục vụ tất cả: Portal React (SPA) + API JSON + các trang Jinja của kiosk.

```
Platform  (waitress :5050  ->  wsgi:app)
├── /                     Portal React — chọn ứng dụng theo quyền
├── /nhan-su, /employees… SPA Quản lý nhân sự
├── /api/auth/*           Đăng nhập CHUNG (JWT + cookie SSO)
├── /api/employees|units|positions|users|roles|audit-logs   Module Nhân sự
├── /api/goiso/*          Module Gọi số (mới)
├── /api/b/*, /api/booking/*, /api/ping, /api/kiosk/*        Tương thích kiosk (X-Branch-Key)
└── /b/<cn>/counter|display|cho, /dat-lich, /admin           Trang Jinja gọi số
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
| P7 | Portal React theo quyền; một cổng phục vụ SPA + API + Jinja | ✅ |
| P8 | Script + tài liệu triển khai, runbook cắt chuyển | ✅ (chờ tên miền + thao tác Cloudflare) |

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
