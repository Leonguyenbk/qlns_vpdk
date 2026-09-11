# Phân hệ Giao việc – Theo dõi nhiệm vụ – Đánh giá KPI

> Tài liệu này là bước khảo sát + phương án tích hợp bắt buộc trước khi viết mã,
> theo đúng trình tự yêu cầu. Nó đối chiếu nội dung tài liệu dự thảo
> `Khung danh gia xep loai chat luong vien chuc VPDKDD Dak Lak Du thao.docx`
> (đã đọc toàn văn — 25 mục + 3 phụ lục, 977 dòng văn bản trích xuất) với hệ
> thống hiện có, để ra quyết định thiết kế và liệt kê điểm còn phải chờ
> Giám đốc VPĐKĐĐ / cấp có thẩm quyền xác nhận.
>
> **Toàn bộ số liệu, hệ số, ngưỡng điểm trong tài liệu dự thảo là DỰ THẢO /
> THÍ ĐIỂM** (căn cứ Nghị định số 233/2026/NĐ-CP CHƯA được đối chiếu với văn
> bản chính thức đã ban hành trong phạm vi phiên làm việc này). Phần mềm vì
> vậy đánh dấu mọi bộ tiêu chí là `DRAFT`/`PILOT` mặc định; không có bộ tiêu
> chí nào được coi là chính thức cho đến khi người có thẩm quyền xác nhận và
> chuyển trạng thái sang `OFFICIAL` trong màn hình quản trị.

## 1. Bảng đối chiếu Nội dung tài liệu – Quy tắc nghiệp vụ – Dữ liệu cần lưu – Chức năng phần mềm – Nội dung còn cần quyết định

| # | Nội dung tài liệu (mục) | Loại nội dung | Quy tắc nghiệp vụ rút ra | Dữ liệu cần lưu | Chức năng phần mềm | Còn cần quyết định |
|---|---|---|---|---|---|---|
| 1 | Mục 3: đối tượng áp dụng (viên chức VPĐKĐĐ + 24 Chi nhánh; NLĐ hợp đồng theo quyết định riêng) | Bắt buộc theo luật (viên chức) / đề xuất riêng (HĐLĐ) | Chấm điểm chỉ áp dụng viên chức đang `WORKING`; HĐLĐ chỉ áp dụng khi phạm vi được khai báo tường minh trong bộ tiêu chí | `Employee.employment_type`, `KpiCriteriaSet.applies_to_contract_labor` | Bộ tiêu chí có cờ áp dụng HĐLĐ, mặc định tắt | #2 phạm vi/phương án áp dụng cho HĐLĐ |
| 2 | Mục 5: nhóm vị trí việc làm (quản lý / không quản lý) | Kế thừa `Position.is_managerial` sẵn có | Nhánh công thức 30/70 khác nhau theo `is_managerial` snapshot tại thời điểm chấm | `KpiScore.is_managerial_snapshot` | Service tự chọn bộ tiêu chí con theo snapshot vị trí | — |
| 3 | Mục 6.3: Khung tiêu chí chung 30đ (Nhóm 1=9/Nhóm 2=9/Nhóm 3=12, đủ tiêu chí con) | Đề xuất thí điểm | Không tự suy luận điểm — mỗi tiêu chí con là **định tính**, phải có người chấm + minh chứng + nhận xét | `kpi_criteria` (cây nhóm→tiêu chí con), `kpi_score_details.evaluator_comment/evidence_refs` | Màn hình chấm điểm định tính bắt buộc nhập người chấm + nhận xét trước khi lưu | #3 phân bổ điểm chi tiết 3 nhóm |
| 4 | Mục 7.2: Khung không quản lý 70đ (SL 20/CL 32/TĐ 18) | Đề xuất thí điểm | 3 công thức định lượng từ dữ liệu nhiệm vụ | `kpi_criteria.formula_key = QUANTITY_RATIO/QUALITY_RATIO/PROGRESS_RATIO` | Engine tính điểm tự động từ `tasks` | #4 trọng số 3 tiêu chí |
| 5 | Mục 8.2: Khung quản lý 70đ (cá nhân 28 = SL8/CL13/TĐ7 + đơn vị 21 + tổ chức 11 + đoàn kết 10) | Đề xuất thí điểm | Nhóm (b)(c)(d) là mức đạt 100%/50%, nhập thủ công có minh chứng (báo cáo đơn vị, Mẫu số 10) — không suy luận từ số liệu nhiệm vụ | `kpi_criteria(kind=MANAGER_UNIT/ORG_CAPABILITY/COHESION)`, `kpi_score_details` | Mẫu nhập mức đạt 100/50/0% + minh chứng | #5 phân bổ điểm 4 nhóm + mức đạt |
| 6 | Mục 9–10: 18 nhóm sản phẩm + sản phẩm chuẩn | Đề xuất thí điểm (danh mục cụ thể: khảo sát thực tế) | Danh mục sản phẩm là danh mục dùng chung nhiều nơi (giao việc, quy đổi, báo cáo) | `product_catalog_groups` (18 nhóm cố định theo Phụ lục II), `products` | Danh mục sản phẩm/công việc trong Giao việc + Admin KPI | #6, #7 danh mục & định mức chi tiết cho từng vị trí |
| 7 | Mục 11: Kn, CAP, 3 mức số lượng (thực tế/quy đổi/ghi nhận sau CAP) | Đề xuất thí điểm, không bắt buộc | Không áp dụng Kn/CAP mặc định minh họa; để trống = không quy đổi (hệ số 1.0, không giới hạn CAP) cho đến khi cấu hình | `product_conversions(kn_value, cap_value, version, status, effective_from/to)` | Admin cấu hình Kn/CAP theo phiên bản, snapshot vào từng nhiệm vụ khi tính điểm | #8 có áp dụng Kn/CAP hay không, hệ số cụ thể |
| 8 | Mục 12: công thức Số lượng | Kế thừa Đề án 2025 | `SL% = Σ(quy đổi hoàn thành, ghi nhận sau CAP) / Σ(quy đổi giao/định mức)`; mẫu số = 0 → "Chưa đủ dữ liệu/Chờ xác nhận", không tự 0%/100% | `kpi_score_details.raw_numerator/raw_denominator/ratio_percent(nullable)` | `kpi_formulas.quantity_ratio()` | Xử lý các trường hợp chưa đến hạn/chuyển kỳ/hủy/đổi phạm vi — đánh dấu "cần xác nhận" (mục 12.2 phần chưa đọc chi tiết trong phiên này) |
| 9 | Mục 13: công thức Chất lượng, thang 5 mức, 4 mức sai sót đất đai | Kế thừa + đề xuất riêng | `CL% = Σ(quy đổi đạt ≥ mức 3/5) / Σ(quy đổi giao/định mức)`; sai sót có mức độ + nguyên nhân + trách nhiệm + minh chứng + khắc phục | `tasks.quality_level(1-5)`, `task_error_records? (gộp vào TaskLog kind=QUALITY_ISSUE + meta)` | Nghiệm thu bắt buộc chấm chất lượng thang 5 trước khi coi là hoàn thành | Trách nhiệm liên đới người phê duyệt — cần quy chế riêng, phần mềm chỉ lưu dữ liệu |
| 10 | Mục 14: công thức Tiến độ, loại trừ thời gian chờ có minh chứng, không trừ điểm trùng SL+TĐ | Kế thừa | `TĐ% = Σ(quy đổi đúng/trước hạn) / Σ(quy đổi giao/định mức)`; loại trừ pause có xác nhận; 1 nguyên nhân không hoàn thành chỉ trừ 1 tiêu chí | `task_pauses(reason_code, evidence_ref, confirmed_by)`, cờ `excluded_from` trên causes | Gộp khoảng nghỉ chồng lấn (merge-interval) trước khi trừ thời gian; cờ loại trừ kép | — |
| 11 | Mục 15: 4 mức xếp loại + điều kiện loại trừ + trần 20%/25% xuất sắc | **Bắt buộc theo luật** (trích Điều 12 NĐ 233/2026) | Ngưỡng điểm KHÔNG tự động ra mức xếp loại — cần xác nhận không vi phạm điều kiện loại trừ + trần tỷ lệ tập thể | `KpiScore.provisional_rating` (chỉ là gợi ý) vs `official_rating` (nhập tay bởi người có thẩm quyền) | Hệ thống chỉ **gợi ý** mức theo ngưỡng, luôn hiển thị cảnh báo "cần xác nhận điều kiện loại trừ & trần tỷ lệ", không tự khóa | #11 cách chọn ai vượt trần khi >20/25% đạt ≥90đ |
| 12 | Mục 16: trường hợp đặc biệt (chưa đủ 6 tháng, nghỉ thai sản, chuyển công tác, kỷ luật) | Bắt buộc theo luật + đề xuất | Không tự động chấm — đánh dấu trạng thái `NOT_RATED` / cần tổng hợp 2 giai đoạn khi đổi vị trí giữa năm | `KpiScore.status = NOT_RATED`, `KpiScore.period_segments (JSON)` cho trường hợp đổi vị trí | Cảnh báo & chặn tự tính khi nhân sự có các mốc đặc biệt trong kỳ | #9 phương án đổi vị trí giữa năm, #10 đang xem xét trách nhiệm |
| 13 | Mục 16.4, 20.3: hủy bỏ/đánh giá lại/thay thế kết quả | Bắt buộc theo luật | Bản ghi cũ KHÔNG xoá — tạo bản ghi mới `replaces_id` trỏ về bản cũ | `KpiScore.replaces_id/replaced_by_id` | Nút "Điều chỉnh kết quả" chỉ tạo bản ghi mới, giữ nguyên bản cũ | — |
| 14 | Mục 17: thẩm quyền theo dõi (khoản 2) vs xếp loại (khoản 3) — tập trung ở Giám đốc VPĐKĐĐ | Bắt buộc theo luật | Phân biệt permission `kpi.review` (theo dõi) và `kpi.approve` (xếp loại) — Trưởng phòng/Giám đốc CN mặc định chỉ có `kpi.review` | `roles`, `permissions` mới | RBAC tách quyền theo đúng bảng 17.1 | #12 có ủy quyền `kpi.approve` cho Giám đốc Chi nhánh hay không |
| 15 | Mục 18: quy trình 13 bước | Bắt buộc (bước 4–10) + đề xuất (1-3, 11-13) | Máy trạng thái `KpiScore.status`: DRAFT→SELF_ASSESSED→REVIEWED→AGGREGATED→APPROVED (khoá kỳ) | `KpiScore.status`, `kpi_evaluation_comments`, `AuditLog(entity_type=kpi_score)` | Màn hình phê duyệt theo từng bước, không cho nhảy bước | #13 thời hạn giải trình cụ thể |
| 16 | Mục 19, 25: 15 biểu mẫu | Đề xuất chuyển hoá | Mỗi mẫu ánh xạ 1 màn hình/1 export, tránh nhập trùng dữ liệu | — | Bảng ánh xạ Mẫu số ↔ màn hình (mục 4 dưới) | #15 hình thức trình bày chính thức |
| 17 | Mục 21: lộ trình thí điểm | Đề xuất | Không có ý nghĩa với phần mềm ngoài việc gắn `status=PILOT` mặc định | — | — | #14 mốc thời gian |
| 18 | Mục 22: 15 nội dung cần quyết định | — | Tổng hợp toàn bộ vào mục 6 tài liệu này | — | Trang "Quy tắc cần xác nhận" trong Admin KPI liệt kê trực tiếp từ CSDL (`kpi_criteria.notes`, `needs_confirmation`) | Toàn bộ #1–#15 |

## 2. Ánh xạ 15 biểu mẫu (Mẫu số 01–15) ↔ màn hình/chức năng

| Mẫu | Tên | Màn hình/chức năng tương ứng | Ghi chú |
|---|---|---|---|
| 01 | Danh mục vị trí việc làm áp dụng đánh giá | Kế thừa `Position` + cờ áp dụng KPI trong Admin KPI | Không tạo danh mục vị trí riêng |
| 02 | Danh mục sản phẩm/công việc | `products` — Admin KPI › Danh mục sản phẩm | |
| 03 | Phiếu xác định sản phẩm chuẩn | `products.is_standard_product` | |
| 04 | Bảng quy đổi sản phẩm/công việc (Kn, CAP) | `product_conversions` — Admin KPI › Quy đổi Kn/CAP | |
| 05 | Phiếu giao nhiệm vụ | `tasks` (tạo/giao việc) | |
| 06 | Nhật ký theo dõi kết quả công việc | `task_logs` (WORK_LOG) + `task_attachments` | Nhiệm vụ không có văn bản vẫn ghi được |
| 07 | Phiếu kê khai sản phẩm/công việc cá nhân theo kỳ | Trang "Công việc của tôi" › tab KPI kỳ hiện tại (tự tổng hợp từ `tasks` đã nghiệm thu) | |
| 08 | Phiếu đánh giá viên chức không giữ chức vụ quản lý | `KpiScore` (is_managerial=false) chi tiết | |
| 09 | Phiếu đánh giá viên chức giữ chức vụ quản lý | `KpiScore` (is_managerial=true) chi tiết | |
| 10 | Phiếu đánh giá kết quả đơn vị/lĩnh vực phụ trách | `kpi_score_details` cho tiêu chí nhóm (b)(c)(d), nhập tại Admin KPI › Đánh giá đơn vị | |
| 11 | Bảng tổng hợp theo dõi tháng/quý | Báo cáo "Tổng hợp theo kỳ" (export Excel) | |
| 12 | Phiếu xếp loại chất lượng viên chức năm | Trang phê duyệt KPI năm (in/PDF) | |
| 13 | Biên bản họp nhận xét, đánh giá | `kpi_evaluation_comments` (author_role_label = biên bản) + đính kèm | |
| 14 | Phiếu đề nghị điều chỉnh kết quả | `kpi_evaluation_comments(type=ADJUSTMENT_REQUEST)` trên trang cá nhân | |
| 15 | Quyết định/Thông báo kết quả xếp loại thay thế | `KpiScore.replaces_id` + xuất bản ghi so sánh cũ/mới | |

## 3. Phương án tích hợp (tóm tắt)

- **Không tạo bảng nhân sự/đăng nhập riêng.** Mọi bảng mới tham chiếu `users.id`
  (người thao tác) và `employees.id` (đối tượng được giao việc/đánh giá) bằng
  khoá ngoại; liên kết account↔hồ sơ tiếp tục dùng `users.employee_id` sẵn có.
- **Snapshot tại thời điểm giao việc/đánh giá**: mỗi `TaskAssignment` và mỗi
  `KpiScore` lưu `unit_id_snapshot/position_id_snapshot/position_name_snapshot/
  is_managerial_snapshot` tại thời điểm tạo — noi theo đúng mẫu đã có ở
  `EmployeeAssignment` (đơn vị/chức vụ "current" chỉ suy ra từ lịch sử, không
  bao giờ ghi đè bản ghi cũ khi nhân sự chuyển đơn vị sau này).
- **Kế thừa RBAC hiện có**: thêm permission `task.*`/`kpi.*` theo đúng quy ước
  `noun.verb`, thêm role mới (không sửa role cũ) và phạm vi đơn vị tiếp tục
  dùng `UnitScopeResolver`/`user_unit_scopes` đã có — không xây cơ chế phân
  quyền song song.
- **Migration**: 1 migration tạo bảng mới (idempotent, kiểm tra tồn tại trước
  khi tạo, không đụng bảng cũ) + 1 migration seed permission/role mới + 18
  nhóm sản phẩm cố định (dữ liệu tham chiếu từ chính tài liệu dự thảo, không
  phải dữ liệu giả) — nối tiếp `0006_goiso_tables`.
- **API/response envelope**: theo đúng chuẩn nhansu hiện có
  (`{success,message,data,errors}`, `success()/paginated()/error()`), tái
  dùng `require_permission`, `resolve_user_scope`, `record_audit`,
  `validated_json`.
- **Giao diện**: thêm nhóm menu "Giao việc & KPI" trong `Layout.jsx`
  (Tổng quan điều hành / Công việc của tôi / Việc tôi đã giao / Danh sách
  nhiệm vụ), và các tab KPI trong `AdminPage.jsx` hiện có — không tạo khung
  ứng dụng mới, giữ Tailwind + tông xanh (`brand.*`/`accent`) sẵn có.
- **Không tự suy diễn** công thức/ngưỡng/hệ số nào ngoài những gì tài liệu nêu
  rõ; mọi chỗ tài liệu chưa chốt được đánh dấu `needs_confirmation=true` ngay
  trong dữ liệu (`kpi_criteria.notes`, `product_conversions.status=DRAFT`) để
  giao diện luôn hiển thị cảnh báo, không ẩn đi.

## 4. Điểm nghiệp vụ chưa rõ / cần xác nhận trước khi vận hành chính thức

Toàn bộ 15 mục tại Mục 22 của tài liệu dự thảo (tổng hợp lại ở bảng mục 1 phía
trên, cột cuối), cộng thêm các điểm phát sinh khi thiết kế phần mềm:

1. Định mức thời gian/khối lượng giao chuẩn cho từng vị trí việc làm — hệ
   thống để trống, người có thẩm quyền nhập qua Admin KPI › Danh mục sản phẩm.
2. Có áp dụng Kn/CAP hay không, giá trị cụ thể — mặc định TẮT (Kn=1, không
   CAP) cho đến khi cấu hình.
3. Trọng số 3 tiêu chí (SL/CL/TĐ) và phân bổ 30đ tiêu chí chung — hệ thống
   dựng sẵn theo đúng số trong tài liệu (20/32/18 và 9/9/12...) nhưng gắn
   `status=DRAFT`, đổi được trong Admin KPI mà không ảnh hưởng kỳ đã khoá.
4. Cơ chế xác định ai được nhận "xuất sắc" khi vượt trần 20%/25% — phần mềm
   chỉ hiển thị danh sách xếp theo điểm giảm dần kèm cảnh báo, không tự chọn.
5. Uỷ quyền `kpi.approve` cho Giám đốc Chi nhánh — mặc định KHÔNG cấp (đúng
   luật, tập trung ở Giám đốc VPĐKĐĐ/role `OFFICE_LEADER`); có thể cấp qua
   Admin › Vai trò nếu có văn bản uỷ quyền.
6. Thời hạn giải trình (mục 20.1) — để cấu hình dạng "số ngày" trong
   `KpiPeriod` thay vì hard-code 05 ngày.
7. Tách quyền "kỹ thuật admin" khỏi "phê duyệt nghiệp vụ": vai trò
   `SYSTEM_ADMIN` hiện tại (kế thừa từ hệ thống cũ) vẫn có mọi permission kỹ
   thuật lẫn nghiệp vụ để hỗ trợ vận hành — khuyến nghị KHÔNG dùng tài khoản
   `SYSTEM_ADMIN` làm người phê duyệt KPI chính thức trong thực tế; việc tách
   bạch triệt để (permission kỹ thuật vs nghiệp vụ) cần thảo luận thêm vì đây
   là thay đổi ảnh hưởng toàn hệ thống hiện có, ngoài phạm vi phân hệ này.
8. Các trường hợp biên khi tính mẫu số Số lượng/Tiến độ (nhiệm vụ chưa đến
   hạn, chuyển kỳ, huỷ do khách quan, đổi phạm vi giữa kỳ) — áp dụng quy tắc
   "tính vào kỳ chứa hạn hoàn thành hiệu lực" (xem `kpi_formulas.py`), đánh
   dấu rõ là quy tắc suy luận riêng của phần mềm (không phải trích dẫn tài
   liệu) và cần Giám đốc VPĐKĐĐ xác nhận khi ban hành Quy chế.

Tất cả các điểm trên hiển thị trực tiếp trong Admin KPI (`/admin/kpi/quy-tac-can-xac-nhan`
sau khi cài đặt) lấy dữ liệu thật từ bảng `kpi_criteria`/`product_conversions`,
không phải nội dung tĩnh viết cứng trong giao diện.
