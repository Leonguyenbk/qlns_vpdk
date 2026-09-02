# Nhập danh sách nhân sự từ file Excel "Phụ lục 4"

Tài liệu này mô tả toàn bộ những gì đã làm để **nhập một file Excel dạng
"THỐNG KÊ VIÊN CHỨC VÀ NGƯỜI LAO ĐỘNG"** ("Phụ lục 4") vào bảng `employees`,
và cách chạy lại khi có file mới.

> TL;DR
> ```bash
> cd backend
> flask --app wsgi db upgrade                       # 1 lần: chạy migration 0003
> flask --app wsgi import-phuluc4 "duong/dan/Phụ lục 4.xlsx" --dry-run   # xem trước
> flask --app wsgi import-phuluc4 "duong/dan/Phụ lục 4.xlsx" --commit    # ghi DB
> ```

---

## 1. Các bước đã thực hiện

| # | Việc | File |
|---|---|---|
| 1 | **Migration `0003_hr_profile_fields`** — thêm 13 cột hồ sơ mở rộng vào `employees`, tạo bảng `employee_education` và `job_grades` | `migrations/versions/0003_hr_profile_fields.py` |
| 2 | Cập nhật model: cột mới trên `Employee`, thêm `EmployeeEducation`, `JobGrade`; `Employee.to_dict()` trả thêm các trường mới | `app/models/employee.py`, `app/models/__init__.py` |
| 3 | Cho phép API tạo/sửa nhân sự nhận các trường mới | `app/schemas/__init__.py`, `app/services/employee_service.py` (`_PROFILE_FIELDS`, `_validate_profile`) |
| 4 | **Bộ nhập** — đọc workbook, dựng cây đơn vị, map chức vụ, tách bằng cấp, upsert nhân sự | `app/imports/phu_luc_4.py` |
| 5 | **Lệnh CLI** `flask --app wsgi import-phuluc4 <path> [--dry-run/--commit] [--sheet] [--as-of]` | `app/__init__.py` (`_register_cli`) |
| 6 | Thêm phụ thuộc `openpyxl==3.1.5` | `requirements.txt` |

Không đụng: API/endpoint hiện có, xác thực, token, phân quyền, `ProtectedRoute`,
seed dữ liệu mẫu, frontend.

---

## 2. Migration 0003 — chi tiết schema

**`employees` (+13 cột, đều nullable):**

| Cột | Kiểu | Nguồn (cột trong sheet) |
|---|---|---|
| `place_of_origin` | VARCHAR(255) | Quê quán |
| `identity_issued_date` | DATE | Ngày cấp CCCD |
| `identity_issued_place` | VARCHAR(255) | Nơi cấp CCCD |
| `job_grade_code` | VARCHAR(30), index | Ngạch / CDNN (mã, vd `V.06.01.02`) |
| `job_grade_name` | VARCHAR(150) | (điền sau từ bảng `job_grades`) |
| `job_duties` | TEXT | Các nhiệm vụ đang đảm nhận |
| `tenure_date` | DATE | Ngày vào biên chế |
| `contract_type` | VARCHAR(50) | Loại hợp đồng — nhãn gốc đã chuẩn hoá |
| `education_level` | VARCHAR(20) | Trình độ CAO NHẤT (ĐH/Ths/CĐ/TC…) |
| `education_major` | VARCHAR(255) | Ngành đào tạo (của bằng cao nhất) |
| `education_mode` | VARCHAR(50) | Hệ đào tạo (Chính quy / VLVH / Từ xa…) |
| `foreign_language_cert` | VARCHAR(100) | Chứng chỉ ngoại ngữ |
| `it_cert` | VARCHAR(100) | Chứng chỉ tin học |

`recruitment_date` (đã có) = **ngày tuyển dụng / ký HĐLĐ**; `tenure_date` (mới) =
**ngày vào biên chế**. Ô sheet thường chỉ có 1 ngày → gán cho cả hai; nếu ô có
2 ngày `dd/mm/yyyy (dd/mm/yyyy)` → ngày đầu = `tenure_date`, ngày sau = `recruitment_date`.

**`employee_education`** — mỗi bằng cấp 1 dòng (người có "Ths, ĐH" → 2 dòng):
`id, employee_id (FK CASCADE), level, major, mode, institution, is_highest`.
Bằng cao nhất được đồng bộ ngược lên `employees.education_*`.

**`job_grades`** — danh mục ngạch: `id, code (unique), name, category` ("Viên chức" / "Hợp đồng").
Bộ nhập **tự thêm mã mới** với `name = NULL`. Điền tên đầy đủ sau (xem §7).

---

## 3. Ánh xạ cột Excel → dữ liệu

Sheet có phần tiêu đề gộp ô ở các dòng 1–11; dữ liệu bắt đầu từ dòng ~12.
Vị trí cột **cố định** (0-based) — khai báo trong `phu_luc_4.py`:

```
0 TT   1 Họ và tên   2 Năm sinh(Nam)  3 Năm sinh(Nữ)   4 Quê quán   5 Nơi ở hiện nay
6 Số CCCD   7 Ngày cấp   8 Nơi cấp   9 Chức vụ/chức danh   10 Nhiệm vụ đang đảm nhận
11 Ngày vào biên chế/(tuyển dụng)   12 Loại HĐ   13 Ngạch(CDNN)
14 Trình độ   15 Ngành đào tạo   16 Hệ đào tạo   17 Ngoại ngữ   18 Tin học
```

> **Nếu file mới đổi thứ tự cột** → sửa hằng `C_*` ở đầu `app/imports/phu_luc_4.py`.

**Giới tính**: suy ra từ **năm sinh nằm ở cột nào** — cột 2 ⇒ `MALE`, cột 3 ⇒ `FEMALE`.

**Loại hợp đồng → nhãn chuẩn + `employment_type` (enum sẵn có):**

| Giá trị gốc | `contract_type` | `employment_type` |
|---|---|---|
| Viên chức | Viên chức | `OFFICIAL` |
| KXĐTH / không xác định thời hạn | HĐLĐ không xác định thời hạn | `CONTRACT` |
| 12 tháng | HĐLĐ 12 tháng | `CONTRACT` |
| thử việc 2 tháng / thử việc | Thử việc… | `PROBATION` |

**Chức vụ (chuỗi tự do) → chức vụ chuẩn** (`positions`), khớp theo thứ tự khoá:
`Phó Giám đốc, Giám đốc, Phó Trưởng phòng, Trưởng phòng, Phó Trưởng bộ phận,
Trưởng bộ phận, Kế toán trưởng, Tổ trưởng, Tổ phó, Thủ quỹ, Văn thư, Chuyên viên, Nhân viên`
(mặc định `Nhân viên`; "Viên chức" → `Chuyên viên`). Chuỗi gốc vẫn được giữ nguyên
ở `employees.professional_title` và `employee_assignments.note`.

---

## 4. Cách bộ nhập dựng CÂY ĐƠN VỊ

Cột "TT" trong sheet **không tin cậy** để phân cấp (dùng lẫn `I`/`V`/`X` cho cả nhóm
cấp cao lẫn mục con). Bộ nhập **phân loại theo TÊN đơn vị**:

| Tên bắt đầu bằng… | Loại đơn vị | Cha | Tên lưu vào DB |
|---|---|---|---|
| `Văn phòng Đăng ký…` | `HEAD_OFFICE` | (gốc) | giữ nguyên |
| `CN …` / `Chi nhánh …` | `BRANCH` | HEAD_OFFICE | giữ nguyên |
| `Phòng …` | `DEPARTMENT` | HEAD_OFFICE | giữ nguyên |
| `Lãnh đạo Văn phòng` / `Ban Giám đốc` | **`DEPARTMENT`** (ngang hàng các phòng) | HEAD_OFFICE | **`Ban Giám đốc`** |
| `Lãnh đạo Chi nhánh` / `Ban Giám đốc` (trong 1 CN) | `SECTION` (ngang hàng các bộ phận) | chi nhánh hiện tại | **`Ban Giám đốc`** |
| `Bộ phận …` / `Tổ …` | `SECTION` | chi nhánh hiện tại (hoặc HEAD_OFFICE) | giữ nguyên |

**Cấp Tổ trong các phòng của Văn phòng tỉnh:** người thuộc 1 trong 4 phòng
(Tổ chức - Hành chính / Kế hoạch - Tài chính / Kỹ thuật - Đăng ký đất đai /
Dữ liệu - thông tin đất đai) được tách xuống **Tổ** (SECTION con của phòng) dựa trên
từ khoá trong cột *nhiệm vụ* / *chức vụ* — bảng `TEAM_RULES` trong `phu_luc_4.py`
(`resolve_team`). Lãnh đạo phòng ("trưởng phòng" / "phó trưởng phòng") và người không
khớp từ khoá nào ở thẳng phòng (dashboard hiện là mục con "(Trực thuộc)").
Chi nhánh **không** tách cấp Tổ (giữ 2 cấp: chi nhánh → bộ phận).
Muốn thêm/sửa tổ cho lần import khác: chỉnh `TEAM_RULES` (key = tên phòng chính xác,
value = danh sách `(từ khoá không dấu, tên Tổ chuẩn)`, khớp theo thứ tự).
| `Khối chi nhánh` / `Các chi nhánh` | (nhãn — bỏ qua) | — | — |

- Đơn vị **idempotent theo `(tên, parent_id)`**; mã sinh tự động từ slug tên
  (`cn-buon-ma-thuot`, `phong-ky-thuat-dang-ky-dat-dai`, …).
- **Hiển thị đơn vị** — `OrganizationUnit` có 3 property, đều trả trong `to_dict()`
  và trong `current_unit` của nhân sự (+ `unit` của phân công):
  - `group_name` — **cột "Phòng / Chi nhánh"**: đơn vị cấp DEPARTMENT/BRANCH gần nhất
    (vd `CN Đồng Xuân`, `Phòng Kế toán`, `Ban Giám đốc`).
  - `section_name` — **cột "Bộ phận"**: chính tên đơn vị nếu là SECTION, ngược lại `null`
    (vd `Bộ phận Kỹ thuật - Đăng ký đất đai`).
  - `path` — chuỗi 1 dòng `group | section` (vd `CN Đồng Xuân | Bộ phận Kỹ thuật…`);
    dùng cho bộ lọc đơn vị, trang chuyển đơn vị, ô chọn đơn vị cha, dashboard.
  Frontend: **danh sách nhân sự** và **lịch sử công tác** tách 2 cột
  *Phòng / Chi nhánh* + *Bộ phận*; trang chi tiết hiển thị 2 dòng tương ứng.
- Ô **cột 10 (J)** trên dòng tiêu đề đơn vị = **tổng số người** của đơn vị → dùng
  để **đối soát**: sau khi nhập, chênh lệch (sheet vs thực đọc) được in ra ở mục
  `⚠ Lệch số lượng`.

Kết quả với file mẫu (Đắk Lắk, 01/9/2026): **742 người**, **127 đơn vị**
(1 văn phòng tỉnh + 5 phòng + 24 chi nhánh + 4 bộ phận/chi nhánh), đối soát khớp
(Phòng Kỹ thuật 57/57, CN Buôn Ma Thuột 83 = 3+23+47+10, …).

---

## 5. Quy tắc upsert (chạy lại nhiều lần an toàn)

- **Khoá trùng lặp = số CCCD** (đã loại bỏ ký tự lạ). Không có CCCD → khoá phụ
  `(họ tên + ngày sinh)`.
- Tồn tại → **cập nhật** các trường hồ sơ (không đụng `status`, không xoá mềm).
  Nếu đơn vị/chức vụ khác phân công chính hiện tại → đóng phân công cũ
  (`end_date = --as-of`) và tạo phân công `REASSIGNMENT` mới.
- Chưa có → **tạo mới**: `employee_code = NS####` (tiếp theo số lớn nhất hiện có),
  `status = WORKING`, tạo 1 phân công chính `RECRUITMENT`
  (`start_date = recruitment_date | tenure_date | --as-of`).
- `employee_education`: **xoá & dựng lại** từ dữ liệu sheet mỗi lần chạy.

Chứng minh idempotent: chạy `--commit` lần 2 trên cùng file →
`tạo mới: 0 · cập nhật: 742 · đơn vị mới: 0`.

---

## 6. Chạy lệnh

```bash
cd backend
# (chỉ lần đầu, sau khi pull code có migration 0003)
flask --app wsgi db upgrade

# XEM TRƯỚC — không ghi gì, in báo cáo + cảnh báo
flask --app wsgi import-phuluc4 "../Phụ lục 4.xlsx" --dry-run --as-of 2026-09-01

# GHI DB
flask --app wsgi import-phuluc4 "../Phụ lục 4.xlsx" --commit --as-of 2026-09-01
```

Tuỳ chọn: `--sheet "Tên sheet"` (mặc định sheet đầu tiên), `--as-of YYYY-MM-DD`
(ngày chốt số liệu, mặc định hôm nay — dùng làm `start_date` khi không có ngày trong ô
và làm `end_date` khi đóng phân công cũ).

**Docker / production:** đảm bảo `openpyxl` đã cài (`pip install -r requirements.txt`),
copy file Excel vào container rồi chạy `flask --app wsgi import-phuluc4 /path/file.xlsx --commit`.

**Nên chạy import vào DB sạch (chỉ có schema + seed vai trò/quyền), KHÔNG chạy
`flask seed`** (seed tạo 33 đơn vị + 15 nhân sự mẫu, sẽ nằm song song với dữ liệu thật).
Nếu DB đã có dữ liệu mẫu: xoá thủ công hoặc nhập vào DB mới.

---

## 6b. Sắp xếp danh sách nhân sự "từ trên xuống"

Danh sách nhân sự mặc định sắp theo **cơ cấu tổ chức**:
Ban Giám đốc (Giám đốc → Phó Giám đốc) → các phòng của Văn phòng tỉnh (theo thứ tự
trong file) → từng chi nhánh (Ban Giám đốc → các bộ phận). Trong mỗi đơn vị: theo
**thứ hạng chức vụ** (`positions.level`: Giám đốc 10, Phó GĐ 20, Trưởng phòng 30,
Phó TP 35, Kế toán trưởng 38, Trưởng BP 40, Phó Trưởng BP 45, Tổ trưởng 50, Tổ phó 55,
Chuyên viên 80, Văn thư/Thủ quỹ 85, Nhân viên 90) rồi tới họ tên.

Cơ chế:
- Migration **0004** thêm `organization_units.sort_index` = thứ tự duyệt cây (DFS).
- `app/services/org_index.py::reindex_units()` tính lại `sort_index`; được gọi tự động
  ở cuối mỗi lần `import-phuluc4` và sau mỗi lần tạo/sửa/xoá đơn vị. Chạy thủ công:
  `flask --app wsgi reindex-units`.
- `positions.level` do bộ nhập gán theo `TITLE_RULES` (đồng bộ lại cả chức vụ đã có).
- API `GET /employees?sort=hierarchy` (mặc định nếu không truyền `sort`). Frontend có
  lựa chọn "Theo cơ cấu tổ chức" và đặt làm mặc định.

> Nếu tự thêm chức vụ mới cần đúng thứ hạng → set `positions.level` cho hợp lý rồi
> không cần reindex (chỉ đơn vị mới cần reindex).

## 6c. Xuất Excel lại theo bố cục "Phụ lục 4"

`GET /api/employees/export` — trả file `.xlsx` dựng đúng bố cục biểu mẫu:
- Khối tiêu đề (tên cơ quan, "Phụ lục 4", tên biểu, dòng "Số liệu … đến ngày …").
- Header cột 3 dòng có merge (Năm sinh → Nam/Nữ, Trình độ chuyên môn cao nhất →
  Trình độ/Ngành/Hệ, Chứng chỉ → Ngoại ngữ/Tin học) + dòng số cột 1..19.
- Nhóm: `A. Văn phòng Đăng ký tỉnh` → `I. Ban Giám đốc` / `II. Phòng …` →
  dòng `- (Trực thuộc)` + `- Tổ …` (số người ở cột J), người đánh số 1..N liên tục
  trong mỗi phòng/bộ phận. Chi nhánh: `B/C… CN X` → `I. Ban Giám đốc` / `II. Bộ phận …`.
- Chân biểu: `Tổng cộng` + tổng số, dòng "…, ngày … tháng … năm YYYY",
  "NGƯỜI LẬP" / "THỦ TRƯỞNG ĐƠN VỊ".
- **Font: Times New Roman toàn bộ** (dữ liệu 12, header cột 11, tên biểu 13) — đặt qua
  helper `_font()` trong `phu_luc_4.py`; đổi cỡ/tên tại đó nếu cần.

**Bộ lọc:** endpoint nhận đúng tham số như `GET /employees`
(`keyword`, `unit_id`, `position_id`, `status`, `employment_type`, `include_deleted`,
`as_of=YYYY-MM-DD`) + phạm vi đơn vị của tài khoản. Có lọc → chỉ xuất người khớp,
mọi số lượng tính lại, thêm dòng "Danh sách đã lọc: …". Không lọc → xuất tất cả.
CCCD chỉ có khi tài khoản có quyền `employee.view_sensitive`.

Code: `app/exports/phu_luc_4.py` (`build_workbook`), `employee_service.export_employees`,
`repo.list_for_export`. Frontend: nút **"Xuất Excel (Phụ lục 4)"** ở trang Danh sách
nhân sự (gửi kèm bộ lọc hiện tại), tải qua `src/lib/download.js`.

## 7. Việc cần làm SAU khi nhập

1. **Điền tên ngạch** cho `job_grades` (bộ nhập chỉ lưu mã). Ví dụ:
   `V.06.01.01` = Địa chính viên hạng I · `V.06.01.02` = hạng II · `V.06.01.03` = hạng III ·
   `V.06.06.17` = Đo đạc bản đồ viên hạng III · `01.003` = Chuyên viên (mã cũ) ·
   `06.031` = Kế toán viên · `13.095` = Kỹ sư (hạng III) · `III`/`IV` = ngạch HĐLĐ.
   ```sql
   UPDATE job_grades SET name = 'Địa chính viên hạng II' WHERE code = 'V.06.01.02';
   ```
2. **Rà mã ngạch lỗi trong nguồn**: `13095` (thiếu dấu chấm, nên gộp về `13.095`),
   `Ao`, `02.014`, `17.147` — kiểm tra lại với file gốc.
3. **Kiểm tra `⚠ Lệch số lượng`** (nếu có) trong báo cáo dry-run — đối chiếu dòng
   tương ứng trong Excel.
4. **Kiểm tra `⚠ Ngày không đọc được`** — các ô ngày ghi sai định dạng
   (vd `29/02/1989` là ngày không tồn tại → bộ nhập rơi về `01/01/1989` + cảnh báo;
   `Năm 2016` → `01/01/2016`).
5. Chức vụ: cột `professional_title` giữ nguyên chuỗi gốc; nếu cần chức vụ chuẩn
   chi tiết hơn (Tổ trưởng Tổ Pháp chế, …) thì bổ sung vào `TITLE_RULES`.

---

## 8. Lỗi dữ liệu đã biết trong file nguồn (bộ nhập tự xử lý)

| Hiện tượng | Cách xử lý |
|---|---|
| `đ`/`Đ` không tách dấu bằng Unicode NFD | `_strip_accents` thay `đ→d`, `Đ→D` trước |
| Ngày kiểu Mỹ `M/D/YYYY` (`5/28/2007`) | nếu tháng > 12 thì hoán đổi ngày↔tháng |
| Ngày chỉ có năm (`Năm 2016`) | lấy năm → `01/01/năm` + cảnh báo |
| Ngày không tồn tại (`29/02/1989`) | rơi về `01/01/năm` + cảnh báo |
| CCCD dính `\n` hoặc `/` ở cuối | lọc chỉ giữ chữ–số |
| Tên bộ phận `Bô phận` (thiếu dấu) | chuẩn hoá về `Bộ phận` |
| Dòng đánh số cột `1 | 2 | 3 …` | bỏ qua (tên toàn chữ số) |
| Hệ đào tạo `Chính quy`/`Chính Quy`/`CQ`/dấu cách thừa | giữ nguyên — **nên** chuẩn hoá thủ công sau |
| Ô cột "chức vụ" lọt giá trị lạ (vd "Cục Cảnh sát QLHC…") | vẫn map → `Nhân viên`, giữ chuỗi gốc ở `professional_title` để rà |

---

## 9. Rollback

```bash
flask --app wsgi db downgrade 0002_seed_roles_permissions   # bỏ cột + 2 bảng mới
```
Migration 0003 `downgrade()` xoá `employee_education`, `job_grades`, index
`ix_employees_job_grade_code` và 13 cột đã thêm.
