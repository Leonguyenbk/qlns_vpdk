# DEPLOYMENT — Triển khai & cắt chuyển

Một tiến trình Waitress phục vụ tất cả (Portal React + toàn bộ giao diện gọi số + API JSON).
Reverse proxy (Cloudflare Tunnel) chỉ chuyển hostname → cổng nội bộ.

## 0. Yêu cầu

- Python 3.12+ (đã chạy tốt trên 3.14 với `SQLAlchemy==2.0.52`).
- Node 20+ để build frontend.
- MySQL 8, một CSDL (mặc định `personnel_management`).
- NSSM (đã có qua chocolatey) để chạy dịch vụ Windows.

## 1. Cấu hình `backend/.env`

```env
FLASK_ENV=production
SECRET_KEY=<chuỗi ngẫu nhiên dài>
JWT_SECRET_KEY=<chuỗi ngẫu nhiên dài khác>
DATABASE_URL=mysql+pymysql://<user>:<pass>@localhost:3306/personnel_management?charset=utf8mb4
CORS_ORIGINS=https://<domain-moi>
APP_DOMAIN=<domain-moi>
COOKIE_DOMAIN=            # để trống nếu 1 domain theo path; đặt .<domain> nếu dùng subdomain
TURNSTILE_SITE_KEY=<cấp lại theo domain mới>
TURNSTILE_SECRET=<...>
GOISO_DB=D:/QUANGTUAN/goiso_kios/hethong_v2.db   # chỉ dùng cho script di trú
```

## 2. Nâng cấp CSDL + nạp dữ liệu (một lần)

```bash
cd backend
.venv\Scripts\flask --app wsgi db upgrade            # tới 0006
.venv\Scripts\python -m scripts.create_admin         # nếu chưa có admin
.venv\Scripts\python -m scripts.migrate_goiso        --source "<hethong_v2.db>" --commit
.venv\Scripts\python -m scripts.migrate_goiso_users  --commit
.venv\Scripts\python -m scripts.link_goiso_units     --commit
```
**Sao lưu trước:** `mysqldump ... --databases personnel_management > backup.sql`.

## 3. Cài dịch vụ platform (không đụng dịch vụ cũ)

```powershell
powershell -File scripts\deploy_platform.ps1 -Port 5050
```
Tạo `PLATFORM_Backend` (Auto) chạy `waitress-serve --port=5050 --threads=48 wsgi:app`,
build `frontend/dist`, kiểm tra `/api/health`.

## 4. Cắt chuyển tên miền (thủ công trên Cloudflare)

Trên **Cloudflare Zero Trust → Tunnels → (tunnel hiện có) → Public hostnames**:

1. Thêm/sửa hostname của **domain mới** → Service `http://127.0.0.1:5050`.
   - Nếu 1 domain theo path: chỉ cần `nhansu-goiso.<domain-moi>` (hoặc gốc) → `:5050`.
   - Nếu giữ subdomain: `goiso.<domain>`, `nhansu.<domain>`, `admin.<domain>` đều → `:5050`.
2. Cập nhật `CORS_ORIGINS` trong `.env` cho khớp, restart `PLATFORM_Backend`.
3. Cấp lại **Turnstile** site key/secret cho domain mới, điền vào `.env`, restart.
4. Kiểm tra qua domain mới: đăng nhập portal, mở nhân sự, mở bàn gọi số, bốc số ở kiosk.

## 5. Ngừng hệ cũ (sau khi xác nhận platform chạy ổn)

```powershell
& $nssm stop QLNS_Backend ;  & $nssm set QLNS_Backend Start SERVICE_DEMAND_START
& $nssm stop QLNS_Nginx   ;  & $nssm set QLNS_Nginx   Start SERVICE_DEMAND_START
# server goiso :5050 cũ: nếu còn chạy thủ công thì tắt tiến trình.
```
Giữ nguyên (không xoá) `D:\DEPLOY\qlns_vpdk`, `D:\QUANGTUAN\goiso_kios`,
`hethong_v2.db` và các bản `mysqldump` ít nhất vài tuần để có đường lùi.

## 6. Lùi (rollback)

1. `nssm stop PLATFORM_Backend`.
2. `nssm set QLNS_Backend Start SERVICE_AUTO_START; nssm start QLNS_Backend` (+ `QLNS_Nginx`).
3. Trỏ Cloudflare hostname về cấu hình cũ.
4. Nếu đã đụng schema: `flask --app wsgi db downgrade 0004` (bỏ bảng `goiso_*` +
   quyền/cột mới) hoặc phục hồi từ `backup.sql`.

## Chạy nhanh (dev)

```bash
cd backend && python app.py            # http://127.0.0.1:5050
cd frontend && npm run dev             # http://127.0.0.1:5173 (proxy /api sang :5050 nếu cần)
```
