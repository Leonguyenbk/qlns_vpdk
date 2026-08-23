-- =====================================================================
-- CSDL NHÂN SỰ - SỞ NÔNG NGHIỆP VÀ MÔI TRƯỜNG
-- Thiết kế dựa trên Mẫu 2C-TCTW/98 (Sơ yếu lý lịch cán bộ, công chức)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. ĐƠN VỊ (cơ cấu tổ chức: Sở -> Chi cục / Phòng ban -> Đơn vị cơ sở)
-- ---------------------------------------------------------------------
CREATE TABLE don_vi (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_don_vi       VARCHAR(20)  UNIQUE NOT NULL,
    ten_don_vi      VARCHAR(255) NOT NULL,
    loai_don_vi     VARCHAR(50),          -- Sở / Chi cục / Phòng / Đơn vị sự nghiệp / Trạm...
    don_vi_cha_id   INTEGER REFERENCES don_vi(id),  -- tự tham chiếu -> cây tổ chức
    dia_chi         VARCHAR(255),
    ghi_chu         TEXT
);

-- ---------------------------------------------------------------------
-- 2. CÁN BỘ, CÔNG CHỨC, VIÊN CHỨC (bảng trung tâm - mục 1-25 của mẫu)
-- ---------------------------------------------------------------------
CREATE TABLE can_bo (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    so_hieu_can_bo              VARCHAR(30) UNIQUE,           -- Số hiệu cán bộ, công chức
    don_vi_id                   INTEGER REFERENCES don_vi(id),
    don_vi_co_so                VARCHAR(255),                 -- Đơn vị cơ sở (nếu khác đơn vị trực thuộc)

    -- (1) Thông tin định danh
    ho_ten_khai_sinh            VARCHAR(150) NOT NULL,
    ten_goi_khac                VARCHAR(150),
    gioi_tinh                   VARCHAR(5),                   -- Nam / Nữ
    anh_chan_dung               VARCHAR(255),                 -- đường dẫn ảnh 4x6

    -- (4)(5)(6)(7) Sinh - Quê quán - Nơi ở - Liên hệ
    ngay_sinh                   DATE,
    noi_sinh                    VARCHAR(255),
    que_quan_xa                 VARCHAR(100),
    que_quan_huyen              VARCHAR(100),
    que_quan_tinh               VARCHAR(100),
    noi_o_hien_nay              VARCHAR(255),
    dien_thoai                  VARCHAR(20),
    email                       VARCHAR(120),

    -- (8)(9)(10)(11) Dân tộc, tôn giáo, thành phần, nghề nghiệp cũ
    dan_toc                     VARCHAR(50),
    ton_giao                    VARCHAR(50),
    thanh_phan_gia_dinh         VARCHAR(255),
    nghe_nghiep_truoc_tuyen_dung VARCHAR(255),

    -- (12)(13) Tuyển dụng
    ngay_tuyen_dung              DATE,
    noi_tuyen_dung                VARCHAR(255),
    ngay_vao_co_quan_hien_tai    DATE,
    ngay_tham_gia_cach_mang      DATE,

    -- (14) Đảng
    ngay_vao_dang                DATE,
    ngay_chinh_thuc_dang         DATE,

    -- (15) Đoàn thể chính trị - xã hội
    ngay_tham_gia_to_chuc_ct_xh  VARCHAR(255),

    -- (16) Quân đội
    ngay_nhap_ngu                 DATE,
    ngay_xuat_ngu                 DATE,
    quan_ham_chuc_vu_cao_nhat     VARCHAR(150),

    -- (17) Trình độ
    trinh_do_giao_duc_pho_thong   VARCHAR(50),
    hoc_ham_hoc_vi_cao_nhat       VARCHAR(150),
    ly_luan_chinh_tri             VARCHAR(50),                -- Sơ cấp/Trung cấp/Cao cấp/Cử nhân
    ngoai_ngu                     VARCHAR(150),

    -- (3)(18)(19)(20) Chức vụ, ngạch, danh hiệu
    cap_uy_hien_tai               VARCHAR(150),
    cap_uy_kiem                   VARCHAR(150),
    chuc_vu                       VARCHAR(255),
    phu_cap_chuc_vu               VARCHAR(50),
    cong_tac_chinh_dang_lam       VARCHAR(255),
    ngach_cong_chuc                VARCHAR(150),
    ma_so_ngach                    VARCHAR(30),
    bac_luong                      VARCHAR(20),
    he_so_luong                    DECIMAL(4,2),
    luong_tu_thang_nam              VARCHAR(20),
    danh_hieu_duoc_phong            VARCHAR(255),

    -- (21) Sở trường
    so_truong_cong_tac              VARCHAR(255),
    cong_viec_lam_lau_nhat           VARCHAR(255),

    -- (24)(25) Sức khỏe, giấy tờ
    tinh_trang_suc_khoe               VARCHAR(100),
    chieu_cao_cm                       DECIMAL(5,1),
    can_nang_kg                        DECIMAL(5,1),
    nhom_mau                           VARCHAR(5),
    so_cmnd_cccd                       VARCHAR(20),
    thuong_binh_loai                   VARCHAR(50),
    gia_dinh_liet_si                   BOOLEAN DEFAULT 0,

    trang_thai                         VARCHAR(30) DEFAULT 'Đang công tác', -- Đang công tác / Nghỉ hưu / Thôi việc / Chuyển công tác
    ngay_tao                           DATETIME DEFAULT CURRENT_TIMESTAMP,
    ngay_cap_nhat                      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 3. ĐÀO TẠO, BỒI DƯỠNG (mục 26)
-- ---------------------------------------------------------------------
CREATE TABLE dao_tao (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    can_bo_id          INTEGER NOT NULL REFERENCES can_bo(id) ON DELETE CASCADE,
    ten_truong         VARCHAR(255),
    nganh_hoc          VARCHAR(255),
    tu_nam             INTEGER,
    den_nam            INTEGER,
    hinh_thuc_hoc      VARCHAR(50),      -- Chính quy / Tại chức / Chuyên tu / Bồi dưỡng
    van_bang_chung_chi VARCHAR(150)      -- Tiến sĩ / Thạc sĩ / Cử nhân / Kỹ sư ...
);

-- ---------------------------------------------------------------------
-- 4. QUÁ TRÌNH CÔNG TÁC (mục 27)
-- ---------------------------------------------------------------------
CREATE TABLE qua_trinh_cong_tac (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    can_bo_id           INTEGER NOT NULL REFERENCES can_bo(id) ON DELETE CASCADE,
    tu_thang_nam        VARCHAR(20),
    den_thang_nam       VARCHAR(20),
    chuc_danh_don_vi    VARCHAR(255)
);

-- ---------------------------------------------------------------------
-- 5. QUÁ TRÌNH LƯƠNG (mục 31 - quá trình lương bản thân)
-- ---------------------------------------------------------------------
CREATE TABLE qua_trinh_luong (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    can_bo_id     INTEGER NOT NULL REFERENCES can_bo(id) ON DELETE CASCADE,
    thang_nam     VARCHAR(20),
    ngach_bac     VARCHAR(100),
    he_so_luong   DECIMAL(4,2)
);

-- ---------------------------------------------------------------------
-- 6. KHEN THƯỞNG (mục 22)
-- ---------------------------------------------------------------------
CREATE TABLE khen_thuong (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    can_bo_id     INTEGER NOT NULL REFERENCES can_bo(id) ON DELETE CASCADE,
    noi_dung      VARCHAR(255),     -- Huân/huy chương, danh hiệu...
    nam           INTEGER
);

-- ---------------------------------------------------------------------
-- 7. KỶ LUẬT (mục 23)
-- ---------------------------------------------------------------------
CREATE TABLE ky_luat (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    can_bo_id         INTEGER NOT NULL REFERENCES can_bo(id) ON DELETE CASCADE,
    hinh_thuc         VARCHAR(150),
    cap_quyet_dinh    VARCHAR(150),
    ly_do             VARCHAR(255),
    nam               INTEGER
);

-- ---------------------------------------------------------------------
-- 8. ĐẶC ĐIỂM LỊCH SỬ BẢN THÂN (mục 28)
-- ---------------------------------------------------------------------
CREATE TABLE lich_su_ban_than (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    can_bo_id     INTEGER NOT NULL REFERENCES can_bo(id) ON DELETE CASCADE,
    loai          VARCHAR(50),   -- 'Bị bắt/bị tù' hoặc 'Làm việc chế độ cũ'
    noi_dung      TEXT
);

-- ---------------------------------------------------------------------
-- 9. QUAN HỆ VỚI NƯỚC NGOÀI (mục 29)
-- ---------------------------------------------------------------------
CREATE TABLE quan_he_nuoc_ngoai (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    can_bo_id     INTEGER NOT NULL REFERENCES can_bo(id) ON DELETE CASCADE,
    loai          VARCHAR(50),   -- 'Tổ chức chính trị/kinh tế/xã hội' hoặc 'Thân nhân ở nước ngoài'
    noi_dung      TEXT
);

-- ---------------------------------------------------------------------
-- 10. QUAN HỆ GIA ĐÌNH (mục 30a - bản thân, 30b - bên vợ/chồng)
-- ---------------------------------------------------------------------
CREATE TABLE quan_he_gia_dinh (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    can_bo_id     INTEGER NOT NULL REFERENCES can_bo(id) ON DELETE CASCADE,
    nhom          VARCHAR(20),    -- 'Bản thân' hoặc 'Bên vợ/chồng'
    quan_he       VARCHAR(30),    -- Bố, Mẹ, Vợ/Chồng, Con, Anh chị em ruột
    ho_ten        VARCHAR(150),
    nam_sinh      INTEGER,
    thong_tin     TEXT            -- quê quán, nghề nghiệp, chức vụ, nơi ở, tổ chức tham gia...
);

-- ---------------------------------------------------------------------
-- 11. HOÀN CẢNH KINH TẾ GIA ĐÌNH (mục 31, 1-1 với can_bo)
-- ---------------------------------------------------------------------
CREATE TABLE hoan_canh_kinh_te (
    can_bo_id                INTEGER PRIMARY KEY REFERENCES can_bo(id) ON DELETE CASCADE,
    nguon_thu_nhap_luong     VARCHAR(255),
    nguon_thu_nhap_khac      VARCHAR(255),
    nha_o_loai               VARCHAR(100),   -- được cấp/được thuê/tự mua/tự xây
    nha_o_dien_tich_m2       DECIMAL(8,2),
    dat_o_duoc_cap_m2        DECIMAL(8,2),
    dat_o_tu_mua_m2          DECIMAL(8,2),
    dat_san_xuat_kinh_doanh  TEXT
);

-- ---------------------------------------------------------------------
-- 12. TÀI KHOẢN NGƯỜI DÙNG HỆ THỐNG (đăng nhập webapp tra cứu/quản trị)
-- ---------------------------------------------------------------------
CREATE TABLE tai_khoan (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_dang_nhap  VARCHAR(50) UNIQUE NOT NULL,
    mat_khau_hash  VARCHAR(255) NOT NULL,
    ho_ten         VARCHAR(150),
    vai_tro        VARCHAR(20) DEFAULT 'viewer',  -- 'admin' | 'editor' | 'viewer'
    can_bo_id      INTEGER REFERENCES can_bo(id)
);

-- ---------------------------------------------------------------------
-- INDEX gợi ý cho tra cứu nhanh
-- ---------------------------------------------------------------------
CREATE INDEX idx_canbo_hoten ON can_bo(ho_ten_khai_sinh);
CREATE INDEX idx_canbo_donvi ON can_bo(don_vi_id);
CREATE INDEX idx_canbo_sohieu ON can_bo(so_hieu_can_bo);
CREATE INDEX idx_canbo_cccd ON can_bo(so_cmnd_cccd);
