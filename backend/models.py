from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ---------------------------------------------------------------- helpers
def _date(d):
    return d.isoformat() if d else None


def _decimal(v):
    return float(v) if v is not None else None


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

    def to_dict(self):
        return {
            "id": self.id,
            "ma_don_vi": self.ma_don_vi,
            "ten_don_vi": self.ten_don_vi,
            "loai_don_vi": self.loai_don_vi,
            "don_vi_cha_id": self.don_vi_cha_id,
            "don_vi_cha_ten": self.cha.ten_don_vi if self.cha else None,
            "dia_chi": self.dia_chi,
            "ghi_chu": self.ghi_chu,
            "si_so": self.si_so,
        }


class CanBo(db.Model):
    __tablename__ = "can_bo"
    id = db.Column(db.Integer, primary_key=True)
    so_hieu_can_bo = db.Column(db.String(30), unique=True)
    don_vi_id = db.Column(db.Integer, db.ForeignKey("don_vi.id"))
    chuc_vu_id = db.Column(db.Integer, db.ForeignKey("chuc_vu.id"))
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

    def to_dict(self, full=False):
        """full=False -> dùng cho danh sách/tra cứu (gọn).
        full=True  -> dùng cho trang chi tiết (đầy đủ mọi trường + bảng con)."""
        data = {
            "id": self.id,
            "so_hieu_can_bo": self.so_hieu_can_bo,
            "ho_ten_khai_sinh": self.ho_ten_khai_sinh,
            "ten_goi_khac": self.ten_goi_khac,
            "gioi_tinh": self.gioi_tinh,
            "ngay_sinh": _date(self.ngay_sinh),
            "tuoi": self.tuoi,
            "chuc_vu": self.chuc_vu,
            "ngach_cong_chuc": self.ngach_cong_chuc,
            "bac_luong": self.bac_luong,
            "trang_thai": self.trang_thai,
            "don_vi_id": self.don_vi_id,
            "don_vi_ten": self.don_vi.ten_don_vi if self.don_vi else None,
            "chuc_vu_id": self.chuc_vu_id,
            "chuc_vu_ten": self.chuc_vu_ref.ten_chuc_vu if self.chuc_vu_ref else None,
            "chuc_vu_cap_bac": self.chuc_vu_ref.cap_bac if self.chuc_vu_ref else None,
        }
        if not full:
            return data

        data.update({
            "don_vi_co_so": self.don_vi_co_so,
            "anh_chan_dung": self.anh_chan_dung,
            "noi_sinh": self.noi_sinh,
            "que_quan_xa": self.que_quan_xa,
            "que_quan_huyen": self.que_quan_huyen,
            "que_quan_tinh": self.que_quan_tinh,
            "noi_o_hien_nay": self.noi_o_hien_nay,
            "dien_thoai": self.dien_thoai,
            "email": self.email,
            "dan_toc": self.dan_toc,
            "ton_giao": self.ton_giao,
            "thanh_phan_gia_dinh": self.thanh_phan_gia_dinh,
            "nghe_nghiep_truoc_tuyen_dung": self.nghe_nghiep_truoc_tuyen_dung,

            "ngay_tuyen_dung": _date(self.ngay_tuyen_dung),
            "noi_tuyen_dung": self.noi_tuyen_dung,
            "ngay_vao_co_quan_hien_tai": _date(self.ngay_vao_co_quan_hien_tai),
            "ngay_tham_gia_cach_mang": _date(self.ngay_tham_gia_cach_mang),
            "ngay_vao_dang": _date(self.ngay_vao_dang),
            "ngay_chinh_thuc_dang": _date(self.ngay_chinh_thuc_dang),
            "ngay_tham_gia_to_chuc_ct_xh": self.ngay_tham_gia_to_chuc_ct_xh,
            "ngay_nhap_ngu": _date(self.ngay_nhap_ngu),
            "ngay_xuat_ngu": _date(self.ngay_xuat_ngu),
            "quan_ham_chuc_vu_cao_nhat": self.quan_ham_chuc_vu_cao_nhat,

            "trinh_do_giao_duc_pho_thong": self.trinh_do_giao_duc_pho_thong,
            "hoc_ham_hoc_vi_cao_nhat": self.hoc_ham_hoc_vi_cao_nhat,
            "ly_luan_chinh_tri": self.ly_luan_chinh_tri,
            "ngoai_ngu": self.ngoai_ngu,

            "cap_uy_hien_tai": self.cap_uy_hien_tai,
            "cap_uy_kiem": self.cap_uy_kiem,
            "phu_cap_chuc_vu": self.phu_cap_chuc_vu,
            "cong_tac_chinh_dang_lam": self.cong_tac_chinh_dang_lam,
            "ma_so_ngach": self.ma_so_ngach,
            "he_so_luong": _decimal(self.he_so_luong),
            "luong_tu_thang_nam": self.luong_tu_thang_nam,
            "danh_hieu_duoc_phong": self.danh_hieu_duoc_phong,

            "so_truong_cong_tac": self.so_truong_cong_tac,
            "cong_viec_lam_lau_nhat": self.cong_viec_lam_lau_nhat,

            "tinh_trang_suc_khoe": self.tinh_trang_suc_khoe,
            "chieu_cao_cm": _decimal(self.chieu_cao_cm),
            "can_nang_kg": _decimal(self.can_nang_kg),
            "nhom_mau": self.nhom_mau,
            "so_cmnd_cccd": self.so_cmnd_cccd,
            "thuong_binh_loai": self.thuong_binh_loai,
            "gia_dinh_liet_si": self.gia_dinh_liet_si,

            "ngay_tao": self.ngay_tao.isoformat() if self.ngay_tao else None,
            "ngay_cap_nhat": self.ngay_cap_nhat.isoformat() if self.ngay_cap_nhat else None,

            "dao_tao": [d.to_dict() for d in self.dao_tao],
            "qua_trinh_cong_tac": [q.to_dict() for q in self.qua_trinh_cong_tac],
            "qua_trinh_luong": [q.to_dict() for q in self.qua_trinh_luong],
            "khen_thuong": [k.to_dict() for k in self.khen_thuong],
            "ky_luat": [k.to_dict() for k in self.ky_luat],
            "lich_su_ban_than": [l.to_dict() for l in self.lich_su_ban_than],
            "quan_he_nuoc_ngoai": [q.to_dict() for q in self.quan_he_nuoc_ngoai],
            "quan_he_gia_dinh": [g.to_dict() for g in self.quan_he_gia_dinh],
            "hoan_canh_kinh_te": self.hoan_canh_kinh_te.to_dict() if self.hoan_canh_kinh_te else None,
        })
        return data
    
class ChucVu(db.Model):
    __tablename__ = "chuc_vu"
    id = db.Column(db.Integer, primary_key=True)
    ten_chuc_vu = db.Column(db.String(150), nullable=False)
    cap_bac = db.Column(db.Integer, nullable=False)
    mo_ta = db.Column(db.String(255))

    can_bo_list = db.relationship("CanBo", backref="chuc_vu_ref", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "ten_chuc_vu": self.ten_chuc_vu,
            "cap_bac": self.cap_bac,
            "mo_ta": self.mo_ta,
            "si_so": len(self.can_bo_list),
        }


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

    def to_dict(self):
        return {
            "id": self.id,
            "ten_truong": self.ten_truong,
            "nganh_hoc": self.nganh_hoc,
            "tu_nam": self.tu_nam,
            "den_nam": self.den_nam,
            "hinh_thuc_hoc": self.hinh_thuc_hoc,
            "van_bang_chung_chi": self.van_bang_chung_chi,
        }


class QuaTrinhCongTac(db.Model):
    __tablename__ = "qua_trinh_cong_tac"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    tu_thang_nam = db.Column(db.String(20))
    den_thang_nam = db.Column(db.String(20))
    chuc_danh_don_vi = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "tu_thang_nam": self.tu_thang_nam,
            "den_thang_nam": self.den_thang_nam,
            "chuc_danh_don_vi": self.chuc_danh_don_vi,
        }


class QuaTrinhLuong(db.Model):
    __tablename__ = "qua_trinh_luong"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    thang_nam = db.Column(db.String(20))
    ngach_bac = db.Column(db.String(100))
    he_so_luong = db.Column(db.Numeric(4, 2))

    def to_dict(self):
        return {
            "id": self.id,
            "thang_nam": self.thang_nam,
            "ngach_bac": self.ngach_bac,
            "he_so_luong": _decimal(self.he_so_luong),
        }


class KhenThuong(db.Model):
    __tablename__ = "khen_thuong"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    noi_dung = db.Column(db.String(255))
    nam = db.Column(db.Integer)

    def to_dict(self):
        return {"id": self.id, "noi_dung": self.noi_dung, "nam": self.nam}


class KyLuat(db.Model):
    __tablename__ = "ky_luat"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    hinh_thuc = db.Column(db.String(150))
    cap_quyet_dinh = db.Column(db.String(150))
    ly_do = db.Column(db.String(255))
    nam = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "hinh_thuc": self.hinh_thuc,
            "cap_quyet_dinh": self.cap_quyet_dinh,
            "ly_do": self.ly_do,
            "nam": self.nam,
        }


class LichSuBanThan(db.Model):
    __tablename__ = "lich_su_ban_than"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    loai = db.Column(db.String(50))
    noi_dung = db.Column(db.Text)

    def to_dict(self):
        return {"id": self.id, "loai": self.loai, "noi_dung": self.noi_dung}


class QuanHeNuocNgoai(db.Model):
    __tablename__ = "quan_he_nuoc_ngoai"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    loai = db.Column(db.String(50))
    noi_dung = db.Column(db.Text)

    def to_dict(self):
        return {"id": self.id, "loai": self.loai, "noi_dung": self.noi_dung}


class QuanHeGiaDinh(db.Model):
    __tablename__ = "quan_he_gia_dinh"
    id = db.Column(db.Integer, primary_key=True)
    can_bo_id = db.Column(db.Integer, db.ForeignKey("can_bo.id"), nullable=False)
    nhom = db.Column(db.String(20))
    quan_he = db.Column(db.String(30))
    ho_ten = db.Column(db.String(150))
    nam_sinh = db.Column(db.Integer)
    thong_tin = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "nhom": self.nhom,
            "quan_he": self.quan_he,
            "ho_ten": self.ho_ten,
            "nam_sinh": self.nam_sinh,
            "thong_tin": self.thong_tin,
        }


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

    def to_dict(self):
        return {
            "nguon_thu_nhap_luong": self.nguon_thu_nhap_luong,
            "nguon_thu_nhap_khac": self.nguon_thu_nhap_khac,
            "nha_o_loai": self.nha_o_loai,
            "nha_o_dien_tich_m2": _decimal(self.nha_o_dien_tich_m2),
            "dat_o_duoc_cap_m2": _decimal(self.dat_o_duoc_cap_m2),
            "dat_o_tu_mua_m2": _decimal(self.dat_o_tu_mua_m2),
            "dat_san_xuat_kinh_doanh": self.dat_san_xuat_kinh_doanh,
        }


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

    def to_dict(self):
        # không bao giờ trả mat_khau_hash ra API
        return {
            "id": self.id,
            "ten_dang_nhap": self.ten_dang_nhap,
            "ho_ten": self.ho_ten,
            "vai_tro": self.vai_tro,
            "can_bo_id": self.can_bo_id,
        }