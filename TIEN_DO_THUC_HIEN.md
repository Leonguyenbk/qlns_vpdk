# Nhật ký tiến độ và bàn giao

> Cập nhật lần cuối: 2026-08-31 (Asia/Ho_Chi_Minh)
>
> Mục đích: ghi lại trạng thái thực tế để model/người tiếp theo có thể tiếp tục nếu phiên làm việc bị ngắt.

## 1. Nguồn yêu cầu đã đọc

- Đã đọc file transcript/bàn giao `2026-08-31-094107-hy-xy-dng-hon-chnh-mt-d-n-web-qun-l-nh.txt`.
- Yêu cầu gốc: hoàn thiện hệ thống quản lý nhân sự giai đoạn 1 bằng Flask + SQLAlchemy/Alembic + MySQL 8 và React/Vite/Tailwind; JWT access/refresh; RBAC kết hợp phạm vi đơn vị; CRUD tài khoản/đơn vị/chức vụ/nhân sự; chuyển đơn vị và giữ lịch sử; giới hạn người giữ chức vụ; nhật ký thao tác; test, Docker và README.
- Phiên trước đã tạo hầu hết source code nhưng hết usage ngay sau khi viết README, chưa kịp chạy kiểm chứng cuối.

## 2. Trạng thái dự án khi tiếp nhận

- Backend có application factory, blueprint theo module, models/services/repositories/permissions, 2 migration, seed, create-admin, test và Dockerfile.
- Frontend có React Router, Axios interceptor, TanStack Query, React Hook Form + Zod, giao diện các module giai đoạn 1, test và Dockerfile/nginx.
- Root có `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`.
- Không thấy `TODO`, `FIXME`, `NotImplemented` hoặc `db.create_all()` trong mã nghiệp vụ.
- Git repository thực tế nằm ở thư mục cha `D:/Python/quanlyns_vpdk`; toàn bộ thư mục `personnel-management` hiện là untracked trong repo cha. Không tự ý commit/reset.

## 3. Kiểm tra đã thực hiện trong phiên này

### Backend

- `python -m compileall -q app tests scripts`: thành công.
- Dùng đúng virtualenv có sẵn: `backend/.venv/Scripts/python.exe`.
- Kết quả cuối `backend/.venv/Scripts/python.exe -m pytest -q`: **33 test passed**.
- Chạy migration trên SQLite kiểm tra riêng (`backend/instance/migration_check.db`):
  - upgrade `0001_initial_schema`: thành công.
  - upgrade `0002_seed_roles_permissions`: thành công.
  - `flask db current`: `0002_seed_roles_permissions (head)`.
- `flask seed`: thành công, tạo 33 đơn vị, 9 chức vụ, 63 cấu hình giới hạn chức vụ, 15 nhân sự và 3 tài khoản mẫu.
- `flask create-admin` với biến môi trường kiểm tra: thành công.

### Frontend

- Phải gọi `npm.cmd` thay vì `npm` do PowerShell chặn `npm.ps1`.
- Kết quả cuối `npm.cmd test -- --run`: **5 test files, 18 tests passed**.
- Kết quả cuối `npm.cmd run build`: thành công, 187 modules transformed; bundle JS khoảng 425.10 kB (gzip 131.54 kB).
- Kết quả cuối `npm.cmd run lint`: thành công, **0 error, 0 warning**.

### Migration/seed kiểm tra tạm

- File `backend/instance/migration_check.db` là database SQLite kiểm tra cục bộ và được `.gitignore` loại trừ qua `instance/`.
- Tài khoản kiểm tra tạo trong database tạm: `admin_check`; mật khẩu chỉ dùng kiểm tra cục bộ và không cần đưa vào cấu hình/source.

## 4. Nội dung đã sửa/hoàn thiện trong phiên này

1. Sửa Axios interceptor: chỉ loại trừ `/auth/login`, `/auth/refresh`, `/auth/logout`; `/auth/me` và `/auth/change-password` được tự refresh khi access token hết hạn. Bổ sung test phân loại endpoint.
2. Bổ sung bộ lọc “Bao gồm hồ sơ đã xóa” ở danh sách nhân sự, nhãn “Đã xóa” và nút khôi phục theo permission; ẩn Sửa/Chuyển/Xóa đối với hồ sơ đã xóa.
3. Bổ sung thao tác Xóa/Ngừng hoạt động chức vụ trên giao diện.
4. Bảo vệ Dashboard bằng `employee.view` để frontend khớp permission backend.
5. Bổ sung `backend/app/schemas/` dùng Marshmallow và nối schema vào route Auth/Employee/Unit/Position/User/Role. Service vẫn kiểm tra quy tắc nghiệp vụ.
6. Chặn tạo/hạ giới hạn chức vụ thấp hơn số người đang giữ; trả payload xung đột rõ ràng và có test hồi quy.
7. Lọc audit log theo `GLOBAL/UNIT/SUBTREE`; tài khoản không global không còn xem nhật ký ngoài phạm vi. Có test hồi quy.
8. Kiểm tra nhân sự liên kết tồn tại khi tạo/cập nhật tài khoản.
9. Bổ sung test CRUD tài khoản/vai trò/phạm vi và đặt lại mật khẩu.
10. Loại bỏ secret/mật khẩu mặc định trong code và `docker-compose.yml`; `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`, mật khẩu MySQL/admin phải lấy từ môi trường. Cập nhật `.env.example` và README.
11. Dọn sạch 2 warning ESLint.
12. Sửa luồng `create-admin`: tài khoản đã tồn tại có thể đặt lại mật khẩu một cách chủ động bằng `ADMIN_RESET_PASSWORD=true`; mặc định vẫn giữ nguyên để không tự đổi mật khẩu sau mỗi lần khởi động.
13. Sửa các input dùng chung để chuyển tiếp `ref` của React Hook Form bằng `forwardRef`; khắc phục lỗi form đăng nhập báo required dù đã nhập. Bổ sung liên kết label/input và test thao tác gõ + nhấn Enter.

## 5. Kiểm tra tích hợp cuối

- Trên database SQLite đã migrate + seed, đăng nhập `admin_check` thành công.
- Các endpoint smoke test đều trả HTTP 200: `/api/auth/me`, `/api/employees`, `/api/employees/dashboard`, `/api/units/tree`, `/api/positions`, `/api/users`, `/api/roles`, `/api/permissions`, `/api/audit-logs`, `/api/health`.
- Quét lại source: không còn `TODO`, `FIXME`, `NotImplemented`, `db.create_all()` hoặc secret mặc định đã biết trong mã chạy.
- Tổng số file dưới `backend/` và `frontend/`: 131 (không tính file bị ignore theo cách liệt kê của `rg`).

## 6. Giới hạn kiểm chứng / việc tùy chọn còn lại

- Máy hiện tại không cài lệnh `docker`, vì vậy chưa thể chạy `docker compose up` hoặc `docker compose config`. YAML và cấu hình đã được rà thủ công; cần chạy Docker Compose trên máy có Docker Desktop để xác nhận đường đi MySQL 8 + nginx thật.
- Migration/seed đã kiểm tra bằng SQLite; chưa có MySQL 8 đang chạy trong môi trường này để kiểm tra khác biệt dialect thực tế.
- Vitest còn in cảnh báo “React Router Future Flag” lên stderr; đây không phải lỗi/test failure và không ảnh hưởng build. Có thể bật future flags khi chuẩn bị nâng React Router v7.
- Thư mục dự án vẫn là `?? personnel-management/` trong repo Git cha. Chưa commit vì người dùng không yêu cầu.
- Không còn hạng mục giai đoạn 1 đã biết đang bị bỏ dở. Các module Giao việc/KPI/Thi đua/Chấm công/Tiền lương vẫn cố ý chưa triển khai đúng yêu cầu.

## 7. Lệnh tiếp tục nhanh

```powershell
# Backend
cd D:\Python\quanlyns_vpdk\personnel-management\backend
.\.venv\Scripts\python.exe -m pytest -q

# Frontend (dùng npm.cmd trên máy này)
cd D:\Python\quanlyns_vpdk\personnel-management\frontend
npm.cmd test -- --run
npm.cmd run build
npm.cmd run lint
```

## 8. Quy tắc an toàn khi tiếp tục

- Không xóa/ghi đè thay đổi ngoài phạm vi vì thư mục dự án đang untracked trong repo cha.
- Không đưa secret/mật khẩu thật vào source; `.env.example` chỉ giữ placeholder bắt buộc thay đổi.
- Không thêm module giao việc, KPI, chấm công hay tiền lương trong giai đoạn 1.
- Các thay đổi đơn vị/chức vụ của nhân sự phải đi qua lịch sử phân công, không sửa trực tiếp lịch sử cũ.
