# MIGRATION — Nạp dữ liệu hệ cũ vào platform

Thứ tự chạy khi triển khai thật (sau khi `flask db upgrade` lên `0006`):

## 1. Dữ liệu gọi số: SQLite → `goiso_*`

```bash
python -m scripts.migrate_goiso --source "D:/QUANGTUAN/goiso_kios/hethong_v2.db"
python -m scripts.migrate_goiso --source "D:/QUANGTUAN/goiso_kios/hethong_v2.db" --commit
```
- Sao chép `branches, config, counters_status, visitor_stats, queue, appointments,
  devices` → `goiso_*`, **giữ nguyên khoá chính**.
- Idempotent (`ON DUPLICATE KEY UPDATE`). Chạy lại chỉ cập nhật.
- In báo cáo: đọc / ghi / lỗi theo từng bảng.

## 2. Tài khoản gọi số → bảng `users` chung

```bash
python -m scripts.migrate_goiso_users            # dry-run
python -m scripts.migrate_goiso_users --commit
```
- `admin` goiso → thêm vai trò `GOISO_ADMIN` cho tài khoản `admin` platform.
- Mỗi nhân viên → `users` cùng username, vai trò `GOISO_COUNTER`,
  `goiso_branch_code = <mã chi nhánh>`, giữ `legacy_password_sha256`
  (đăng nhập lần đầu tự đổi sang Argon2).
- Báo cáo: nguồn / tạo / cập nhật / bỏ qua / lỗi.

## 3. Liên kết đơn vị ↔ chi nhánh gọi số

```bash
python -m scripts.link_goiso_units            # dry-run, in bảng đối chiếu
python -m scripts.link_goiso_units --commit
```
- Khớp `organization_units` (unit_type=BRANCH) với `goiso_branches` theo tên
  chuẩn hoá (bỏ "CN ", bỏ dấu, bỏ dấu nháy). Ghi `organization_units.goiso_branch_code`.
- In danh sách không khớp cả hai chiều để rà tay.

## Kết quả kiểm thử (dev, 2026-09-10)

| Bước | Kết quả |
|---|---|
| migrate_goiso | 155 dòng, 0 lỗi (24 chi nhánh, 98 config, 15 queue, 2 lịch hẹn, 3 thiết bị) |
| migrate_goiso_users | 12 tài khoản (1 admin += GOISO_ADMIN, 11 GOISO_COUNTER @ bmt) |
| link_goiso_units | 24/24 đơn vị BRANCH khớp chi nhánh goiso |

## Lùi lại

`scripts/migrate_goiso*.py` không xoá gì ở nguồn SQLite. Nếu cần bỏ dữ liệu goiso
đã nạp: `flask db downgrade 0005` (xoá toàn bộ bảng `goiso_*` và cột liên kết).
Luôn có bản `mysqldump` trước khi nâng cấp (xem DATABASE.md).
