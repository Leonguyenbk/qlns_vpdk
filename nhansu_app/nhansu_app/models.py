from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class DonVi(db.Model):
    __tablename__ = "don_vi"
    id = db.Column(db.Integer, primary_key=True)
    ma_don_vi = db.Column(db.String(20), unique=True, nullable=False)
    ten_don_vi = db.Column(db.String(255), nullable=False)
    loai_don_vi = db.Column(db.String(50))
    don_vi_cha_id = db.Column(db.Integer, db.ForeignKey("don_vi.id"))
    dia_chi = db.Column(db.String(255))
    ghi_chu = db.Column(db.Text)

    con = db.relationship("DonVi", backref=db.backref("cha", remote_side=[id]))
    can_bo_list = db.relationship("CanBo", backref="don_vi", lazy=True)

    @property
    def si_so(self):
        return len(self.can_bo_list)


class CanBo(db.Model):
    __tablename__ = "can_bo"
    id = db.Column(db.Integer, primary_key=True)
    so_hieu_can_bo = db.Column(db.String(30), unique=True)
    don_vi_id = db.Column(db.Integer, db.ForeignKey("don_vi.id"))
    don_vi_co_so = db.Column(db.String(255))

    ho_ten_khai_sinh = db.Column(db.String(150), nullable=False)
    ten_goi_khac = db.Column(db.String(150))
    gioi_tinh = db.Column(db.String(5))
    anh_chan_dung = db.Column(db.String(255))

    ngay_sinh = db.Column(db.Date)
    noi_sinh = db.Column(db.String(255))
    que_quan_xa = db.Column(db.String(100))
    que_quan_huyen = db.Column(db.String(100))
    que_quan_tinh = db.Column(db.String(100))
    noi_o_hien_nay = db.Column(db.String(255))
    dien_thoai = db.Column(db.String(20))
    email = db.Column(db.String(120))

    dan_toc = db.Column(db.String(50))
    ton_giao = db.Column(db.String(50))
    thanh_phan_gia_dinh = db.Column(db.String(255))
    nghe_nghiep_truoc_tuyen_dung = db.Column(db.String(255))

    ngay_tuyen_dung = db.Column(db.Date)
    noi_tuyen_dung = db.Column(db.String(255))
    ngay_vao_co_quan_hien_tai = db.Column(db.Date)
    ngay_tham_gia_cach_mang = db.Column(db.Date)

    ngay_vao_dang = db.Column(db.Date)
    ngay_chinh_thuc_dang = db.Column(db.Date)

    ngay_tham_gia_to_chuc_ct_xh = db.Column(db.String(255))

    ngay_nhap_ngu = db.Column(db.Date)
    ngay_xuat_ngu = db.Column(db.Date)
    quan_ham_chuc_vu_cao_nhat = db.Column(db.String(150))

    trinh_do_giao_duc_pho_thong = db.Column(db.String(50))
    hoc_ham_hoc_vi_cao_nhat = db.Column(db.String(150))
    ly_luan_chinh_tri = db.Column(db.String(50))
    ngoai_ngu = db.Column(db.String(150))

    cap_uy_hien_tai = db.Column(db.String(150))
    cap_uy_kiem = db.Column(db.String(150))
    chuc_vu = db.Column(db.String(255))
    phu_cap_chuc_vu = db.Column(db.String(50))
    cong_tac_chinh_dang_lam = db.Column(db.String(255))
    ngach_cong_chuc = db.Column(db.String(150))
    ma_so_ngach = db.Column(db.String(30))
    bac_luong = db.Column(db.String(20))
    he_so_luong = db.Column(db.Numeric(4, 2))
    luong_tu_thang_nam = db.Column(db.String(20))
    danh_hieu_duoc_phong = db.Column(db.String(255))

    so_truong_cong_tac = db.Column(db.String(255))
    cong_viec_lam_lau_nhat = db.Column(db.String(255))

    tinh_trang_suc_khoe = db.Column(db.String(100))
    chieu_cao_cm = db.Column(db.Numeric(5, 1))
    can_nang_kg = db.Column(db.Numeric(5, 1))
    nhom_mau = db.Column(db.String(5))
    so_cmnd_cccd = db.Column(db.String(20))
    thuong_binh_loai = db.Column(db.String(50))
    gia_dinh_liet_si = db.Column(db.Boolean, default=False)

    trang_thai = db.Column(db.String(30), default="Đang công tác")
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)
    ngay_cap_nhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dao_tao = db.relationship("DaoTao", backref="can_bo", cascade="all, delete-orphan", lazy=True)
    qua_trinh_cong_tac = db.relationship("QuaTrinhCongTac", backref="can_bo", cascade="all, delete-orphan", lazy=True)
    qua_trinh_luong = db.relationship("QuaTrinhLuong", backref="can_bo", cascade="all, delete-orphan", lazy=True)
    khen_thuong = db.relationship("KhenThuong", backref="can_bo", cascade="all, delete-orphan", lazy=True)
    ky_luat = db.relationship("KyLuat", backref="can_bo", cascade="all, delete-orphan", lazy=True)
    lich_su_ban_than = db.relationship("LichSuBanThan", backref="can_bo", cascade="all, delete-orphan", lazy=True)
    quan_he_nuoc_ngoai = db.relationship("QuanHeNuocNgoai", backref="can_bo", cascade="all, delete-orphan", lazy=True)
    quan_he_gia_dinh = db.relationship("QuanHeGiaDinh", backref="can_bo", cascade="all, delete-orphan", lazy=True)
    hoan_canh_kinh_te = db.relationship("HoanCanhKinhTe", backref="can_bo", uselist=False, cascade="all, delete-orphan")

    @property
    def tuoi(self):
        if not self.ngay_sinh:
            return None
        today = datetime.today()
        return today.year - self.ngay_sinh.year - ((today.month, today.day) < (self.ngay_sinh.month, self.ngay_sinh.day))


class DaoTao(db.Model):
    __tablename__ = "dao_tao"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    ten_truong = db.Column(db.String(255))
    nganh_hoc = db.Column(db.String(255))
    tu_nam = db.Column(db.Integer)
    den_nam = db.Column(db.Integer)
    hinh_thuc_hoc = db.Column(db.String(50))
    van_bang_chung_chi = db.Column(db.String(150))


class QuaTrinhCongTac(db.Model):
    __tablename__ = "qua_trinh_cong_tac"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    tu_thang_nam = db.Column(db.String(20))
    den_thang_nam = db.Column(db.String(20))
    chuc_danh_don_vi = db.Column(db.String(255))


class QuaTrinhLuong(db.Model):
    __tablename__ = "qua_trinh_luong"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    thang_nam = db.Column(db.String(20))
    ngach_bac = db.Column(db.String(100))
    he_so_luong = db.Column(db.Numeric(4, 2))


class KhenThuong(db.Model):
    __tablename__ = "khen_thuong"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    noi_dung = db.Column(db.String(255))
    nam = db.Column(db.Integer)


class KyLuat(db.Model):
    __tablename__ = "ky_luat"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    hinh_thuc = db.Column(db.String(150))
    cap_quyet_dinh = db.Column(db.String(150))
    ly_do = db.Column(db.String(255))
    nam = db.Column(db.Integer)


class LichSuBanThan(db.Model):
    __tablename__ = "lich_su_ban_than"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    loai = db.Column(db.String(50))
    noi_dung = db.Column(db.Text)


class QuanHeNuocNgoai(db.Model):
    __tablename__ = "quan_he_nuoc_ngoai"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    loai = db.Column(db.String(50))
    noi_dung = db.Column(db.Text)


class QuanHeGiaDinh(db.Model):
    __tablename__ = "quan_he_gia_dinh"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    nhom = db.Column(db.String(20))
    quan_he = db.Column(db.String(30))
    ho_ten = db.Column(db.String(150))
    nam_sinh = db.Column(db.Integer)
    thong_tin = db.Column(db.Text)


class HoanCanhKinhTe(db.Model):
    __tablename__ = "hoan_canh_kinh_te"
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), primary_key=True)
    nguon_thu_nhap_luong = db.Column(db.String(255))
    nguon_thu_nhap_khac = db.Column(db.String(255))
    nha_o_loai = db.Column(db.String(100))
    nha_o_dien_tich_m2 = db.Column(db.Numeric(8, 2))
    dat_o_duoc_cap_m2 = db.Column(db.Numeric(8, 2))
    dat_o_tu_mua_m2 = db.Column(db.Numeric(8, 2))
    dat_san_xuat_kinh_doanh = db.Column(db.Text)


class TaiKhoan(db.Model):
    __tablename__ = "tai_khoan"
    id = db.Column(db.Integer, primary_key=True)
    ten_dang_nhap = db.Column(db.String(50), unique=True, nullable=False)
    mat_khau_hash = db.Column(db.String(255), nullable=False)
    ho_ten = db.Column(db.String(150))
    vai_tro = db.Column(db.String(20), default="viewer")
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"))

    def set_password(self, mat_khau):
        self.mat_khau_hash = generate_password_hash(mat_khau)

    def check_password(self, mat_khau):
        return check_password_hash(self.mat_khau_hash, mat_khau)
