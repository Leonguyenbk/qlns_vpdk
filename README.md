# Platform — Hệ thống hợp nhất Gọi số (goiso) + Quản lý nhân sự

Hợp nhất hai hệ thống thành **một backend Flask + một tiến trình Waitress**, module hoá rõ ràng:

```
Platform
├── Auth chung (JWT, RBAC, scope theo cây đơn vị)
├── Module Nhân sự   (/api/employees, /api/units, /api/positions, ...)
├── Module Goiso      (/api/goiso/*  + lớp tương thích /api/b, /api/booking, /api/ping, /api/kiosk)
├── Admin chung       (/api/users, /api/roles, /api/audit-logs)
└── Shared/Common     (response chuẩn, error handler, logging, permissions)
```

Nguồn gốc & kế hoạch hợp nhất: **[docs/MERGE_ANALYSIS.md](docs/MERGE_ANALYSIS.md)**.

## Trạng thái theo phase

| Phase | Nội dung | Trạng thái |
|---|---|---|
| P1 | Phân tích 2 codebase, chốt kiến trúc | ✅ xong |
| P2 | Dựng khung platform từ backend nhân sự, chạy cổng riêng | ✅ xong (backend + test) |
| P3 | Đưa goiso vào `modules/goiso` (giữ SQLite tạm) + lớp tương thích | ✅ xong |
| P4 | Chuẩn hoá module nhân sự trong cấu trúc mới + test nghiệp vụ | ✅ xong |
| P5 | Gộp tài khoản/đăng nhập, permission `GOISO_*`, cookie SSO cho trang Jinja | ⏳ |
| P6 | Đơn vị dùng chung; chuyển bảng goiso sang MySQL (`goiso_*`) có script + log | ⏳ |
| P7 | Portal React (chọn ứng dụng theo quyền) + màn quản trị goiso trong SPA | ⏳ |
| P8 | Triển khai: 1 Waitress, NSSM, nginx, Cloudflare Tunnel domain mới, docs | ⏳ |

## Chạy (development)

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env   # rồi sửa DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY
python app.py            # http://127.0.0.1:5000  (hoặc PORT trong môi trường)
```

## Chạy (production)

```bash
waitress-serve --host=0.0.0.0 --port=5050 wsgi:app
```

Frontend (React SPA):

```bash
cd frontend
npm ci
npm run build     # -> frontend/dist  (nginx phục vụ, proxy /api & /b -> :5050)
```

## Kiểm thử

```bash
cd backend
set FLASK_ENV=testing && .venv\Scripts\pytest -q
```

## Lưu ý

- Hai hệ cũ vẫn giữ nguyên tại `D:\DEPLOY\qlns_vpdk` và `D:\QUANGTUAN\goiso_kios` làm nguồn + phương án lùi cho tới khi platform chạy thật ổn.
- `backend/.env` **không** commit. CSDL thật (chứa CCCD) không đưa lên git.
- Phase 2 tạm trỏ `DATABASE_URL` vào CSDL nhân sự đang chạy; Phase 6 tách CSDL `qlns_platform` riêng.
