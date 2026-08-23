# CSDL Nhân sự — Sở Nông nghiệp và Môi trường

Ứng dụng web (Flask) quản lý & tra cứu hồ sơ cán bộ, công chức, viên chức, xây dựng dựa trên
Mẫu 2C-TCTW/98 (Sơ yếu lý lịch cán bộ, công chức).

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy ứng dụng

```bash
python app.py
```

Lần chạy đầu tiên, ứng dụng tự động:
- Tạo file CSDL SQLite `nhansu.db` theo đúng lược đồ trong `schema.sql`
- Tạo tài khoản quản trị: **admin / admin123**
- Tạo sẵn Sở và 5 đơn vị trực thuộc mẫu (Văn phòng, Phòng TCCB, Chi cục Thủy lợi, Chi cục BVMT, Chi cục Kiểm lâm)

Mở trình duyệt tại: http://127.0.0.1:5000

## Cấu trúc dự án

```
app.py            - Flask app: routes, xử lý form, xác thực
models.py         - SQLAlchemy models (ánh xạ từ schema.sql)
schema.sql         - Thiết kế CSDL đầy đủ (DDL tham chiếu, dùng cho MySQL/PostgreSQL/SQLite)
templates/          - Giao diện Jinja2
static/css/          - CSS (bảng màu xanh lá/đất/nước theo chủ đề Nông nghiệp - Môi trường)
```

## Phân quyền tài khoản

| Vai trò | Quyền |
|---|---|
| `admin`  | Toàn quyền: thêm/sửa/xóa hồ sơ, quản lý đơn vị |
| `editor` | Thêm/sửa hồ sơ, không xóa được, không quản lý đơn vị |
| `viewer` | Chỉ tra cứu, xem chi tiết |

Tạo thêm tài khoản: dùng shell Python với `TaiKhoan`, hoặc bổ sung màn hình quản lý người dùng sau này.

## Mô hình dữ liệu (tóm tắt)

- **don_vi** — cơ cấu tổ chức (Sở → Chi cục/Phòng → Đơn vị cơ sở), cây tự tham chiếu
- **can_bo** — hồ sơ chính (mục 1–25 của mẫu): thông tin cá nhân, Đảng, chức vụ, ngạch/bậc lương, sức khỏe...
- **dao_tao** — mục 26: quá trình đào tạo, bồi dưỡng
- **qua_trinh_cong_tac** — mục 27: tóm tắt quá trình công tác
- **qua_trinh_luong** — lịch sử ngạch/bậc/hệ số lương
- **khen_thuong** / **ky_luat** — mục 22, 23
- **lich_su_ban_than** — mục 28: bị bắt/bị tù, làm việc chế độ cũ
- **quan_he_nuoc_ngoai** — mục 29
- **quan_he_gia_dinh** — mục 30a, 30b: bố mẹ, vợ/chồng, con, anh chị em ruột (cả hai bên)
- **hoan_canh_kinh_te** — mục 31: thu nhập, nhà đất (quan hệ 1-1 với can_bo)
- **tai_khoan** — tài khoản đăng nhập hệ thống

## Mở rộng gợi ý

- Xuất PDF sơ yếu lý lịch đúng mẫu 2C-TCTW/98 từ trang chi tiết
- Nhập liệu hàng loạt từ Excel (danh sách cán bộ hiện có)
- Nhắc lịch: nâng ngạch/bậc lương, hết hạn hợp đồng, nghỉ hưu
- Thống kê theo đơn vị, độ tuổi, trình độ, giới tính (biểu đồ)
- Đổi sang PostgreSQL/MySQL khi triển khai thật (đã có `schema.sql` chuẩn)
