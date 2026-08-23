import os
from datetime import datetime, date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from sqlalchemy import or_

from models import (
    db, DonVi, CanBo, DaoTao, QuaTrinhCongTac, QuaTrinhLuong,
    KhenThuong, KyLuat, LichSuBanThan, QuanHeNuocNgoai, QuanHeGiaDinh,
    HoanCanhKinhTe, TaiKhoan
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'nhansu.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "sono-mtnn-doi-secret-key-demo"

db.init_app(app)


# ---------------------------------------------------------------- helpers
def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_decimal(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login", next=request.path))
            if session.get("role") not in roles:
                flash("Bạn không có quyền thực hiện thao tác này.", "error")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_globals():
    return {"current_user_role": session.get("role"), "current_user_name": session.get("ho_ten")}


# ---------------------------------------------------------------- auth
@app.route("/dang-nhap", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("ten_dang_nhap", "").strip()
        password = request.form.get("mat_khau", "")
        tk = TaiKhoan.query.filter_by(ten_dang_nhap=username).first()
        if tk and tk.check_password(password):
            session["user_id"] = tk.id
            session["role"] = tk.vai_tro
            session["ho_ten"] = tk.ho_ten or tk.ten_dang_nhap
            flash(f"Chào mừng {session['ho_ten']}!", "success")
            return redirect(request.args.get("next") or url_for("index"))
        flash("Sai tên đăng nhập hoặc mật khẩu.", "error")
    return render_template("login.html")


@app.route("/dang-xuat")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------- dashboard / tra cứu
@app.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    don_vi_id = request.args.get("don_vi_id", type=int)
    trang_thai = request.args.get("trang_thai", "").strip()

    query = CanBo.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            CanBo.ho_ten_khai_sinh.ilike(like),
            CanBo.so_hieu_can_bo.ilike(like),
            CanBo.so_cmnd_cccd.ilike(like),
            CanBo.chuc_vu.ilike(like),
        ))
    if don_vi_id:
        query = query.filter(CanBo.don_vi_id == don_vi_id)
    if trang_thai:
        query = query.filter(CanBo.trang_thai == trang_thai)

    ds_can_bo = query.order_by(CanBo.ho_ten_khai_sinh).all()
    don_vi_list = DonVi.query.order_by(DonVi.ten_don_vi).all()

    return render_template(
        "index.html",
        ds_can_bo=ds_can_bo,
        don_vi_list=don_vi_list,
        q=q, don_vi_id=don_vi_id, trang_thai=trang_thai,
        tong_so=CanBo.query.count(),
    )


# ---------------------------------------------------------------- chi tiết
@app.route("/can-bo/<int:id>")
@login_required
def chi_tiet(id):
    cb = CanBo.query.get_or_404(id)
    return render_template("detail.html", cb=cb)


# ---------------------------------------------------------------- thêm / sửa
@app.route("/can-bo/moi", methods=["GET", "POST"])
@role_required("admin", "editor")
def them_moi():
    if request.method == "POST":
        cb = CanBo()
        luu_form_can_bo(cb)
        db.session.add(cb)
        db.session.commit()
        flash("Đã thêm hồ sơ mới.", "success")
        return redirect(url_for("chi_tiet", id=cb.id))
    don_vi_list = DonVi.query.order_by(DonVi.ten_don_vi).all()
    return render_template("form.html", cb=None, don_vi_list=don_vi_list)


@app.route("/can-bo/<int:id>/sua", methods=["GET", "POST"])
@role_required("admin", "editor")
def sua(id):
    cb = CanBo.query.get_or_404(id)
    if request.method == "POST":
        luu_form_can_bo(cb)
        db.session.commit()
        flash("Đã cập nhật hồ sơ.", "success")
        return redirect(url_for("chi_tiet", id=cb.id))
    don_vi_list = DonVi.query.order_by(DonVi.ten_don_vi).all()
    return render_template("form.html", cb=cb, don_vi_list=don_vi_list)


@app.route("/can-bo/<int:id>/xoa", methods=["POST"])
@role_required("admin")
def xoa(id):
    cb = CanBo.query.get_or_404(id)
    db.session.delete(cb)
    db.session.commit()
    flash("Đã xóa hồ sơ.", "success")
    return redirect(url_for("index"))


def luu_form_can_bo(cb):
    f = request.form
    cb.so_hieu_can_bo = f.get("so_hieu_can_bo") or None
    cb.don_vi_id = parse_int(f.get("don_vi_id"))
    cb.don_vi_co_so = f.get("don_vi_co_so")
    cb.ho_ten_khai_sinh = f.get("ho_ten_khai_sinh")
    cb.ten_goi_khac = f.get("ten_goi_khac")
    cb.gioi_tinh = f.get("gioi_tinh")
    cb.ngay_sinh = parse_date(f.get("ngay_sinh"))
    cb.noi_sinh = f.get("noi_sinh")
    cb.que_quan_xa = f.get("que_quan_xa")
    cb.que_quan_huyen = f.get("que_quan_huyen")
    cb.que_quan_tinh = f.get("que_quan_tinh")
    cb.noi_o_hien_nay = f.get("noi_o_hien_nay")
    cb.dien_thoai = f.get("dien_thoai")
    cb.email = f.get("email")
    cb.dan_toc = f.get("dan_toc")
    cb.ton_giao = f.get("ton_giao")
    cb.thanh_phan_gia_dinh = f.get("thanh_phan_gia_dinh")
    cb.nghe_nghiep_truoc_tuyen_dung = f.get("nghe_nghiep_truoc_tuyen_dung")
    cb.ngay_tuyen_dung = parse_date(f.get("ngay_tuyen_dung"))
    cb.noi_tuyen_dung = f.get("noi_tuyen_dung")
    cb.ngay_vao_co_quan_hien_tai = parse_date(f.get("ngay_vao_co_quan_hien_tai"))
    cb.ngay_tham_gia_cach_mang = parse_date(f.get("ngay_tham_gia_cach_mang"))
    cb.ngay_vao_dang = parse_date(f.get("ngay_vao_dang"))
    cb.ngay_chinh_thuc_dang = parse_date(f.get("ngay_chinh_thuc_dang"))
    cb.ngay_tham_gia_to_chuc_ct_xh = f.get("ngay_tham_gia_to_chuc_ct_xh")
    cb.ngay_nhap_ngu = parse_date(f.get("ngay_nhap_ngu"))
    cb.ngay_xuat_ngu = parse_date(f.get("ngay_xuat_ngu"))
    cb.quan_ham_chuc_vu_cao_nhat = f.get("quan_ham_chuc_vu_cao_nhat")
    cb.trinh_do_giao_duc_pho_thong = f.get("trinh_do_giao_duc_pho_thong")
    cb.hoc_ham_hoc_vi_cao_nhat = f.get("hoc_ham_hoc_vi_cao_nhat")
    cb.ly_luan_chinh_tri = f.get("ly_luan_chinh_tri")
    cb.ngoai_ngu = f.get("ngoai_ngu")
    cb.cap_uy_hien_tai = f.get("cap_uy_hien_tai")
    cb.cap_uy_kiem = f.get("cap_uy_kiem")
    cb.chuc_vu = f.get("chuc_vu")
    cb.phu_cap_chuc_vu = f.get("phu_cap_chuc_vu")
    cb.cong_tac_chinh_dang_lam = f.get("cong_tac_chinh_dang_lam")
    cb.ngach_cong_chuc = f.get("ngach_cong_chuc")
    cb.ma_so_ngach = f.get("ma_so_ngach")
    cb.bac_luong = f.get("bac_luong")
    cb.he_so_luong = parse_decimal(f.get("he_so_luong"))
    cb.luong_tu_thang_nam = f.get("luong_tu_thang_nam")
    cb.danh_hieu_duoc_phong = f.get("danh_hieu_duoc_phong")
    cb.so_truong_cong_tac = f.get("so_truong_cong_tac")
    cb.cong_viec_lam_lau_nhat = f.get("cong_viec_lam_lau_nhat")
    cb.tinh_trang_suc_khoe = f.get("tinh_trang_suc_khoe")
    cb.chieu_cao_cm = parse_decimal(f.get("chieu_cao_cm"))
    cb.can_nang_kg = parse_decimal(f.get("can_nang_kg"))
    cb.nhom_mau = f.get("nhom_mau")
    cb.so_cmnd_cccd = f.get("so_cmnd_cccd")
    cb.thuong_binh_loai = f.get("thuong_binh_loai")
    cb.gia_dinh_liet_si = bool(f.get("gia_dinh_liet_si"))
    cb.trang_thai = f.get("trang_thai") or "Đang công tác"

    # --- các bảng con: xóa hết rồi thêm lại theo dữ liệu form (đơn giản, đủ dùng cho form động) ---
    def sync_rows(model, rows, build_fn):
        model.query.filter_by(can_bo_id=cb.id).delete() if cb.id else None
        for row in rows:
            obj = build_fn(row)
            if obj:
                obj.can_bo_id = cb.id
                db.session.add(obj)

    if cb.id is None:
        db.session.add(cb)
        db.session.flush()  # lấy cb.id trước khi thêm bảng con

    # Đào tạo bồi dưỡng
    ten_truong = f.getlist("dt_ten_truong")
    nganh_hoc = f.getlist("dt_nganh_hoc")
    tu_nam = f.getlist("dt_tu_nam")
    den_nam = f.getlist("dt_den_nam")
    hinh_thuc = f.getlist("dt_hinh_thuc")
    van_bang = f.getlist("dt_van_bang")
    DaoTao.query.filter_by(can_bo_id=cb.id).delete()
    for i in range(len(ten_truong)):
        if ten_truong[i].strip():
            db.session.add(DaoTao(
                can_bo_id=cb.id, ten_truong=ten_truong[i], nganh_hoc=nganh_hoc[i],
                tu_nam=parse_int(tu_nam[i]), den_nam=parse_int(den_nam[i]),
                hinh_thuc_hoc=hinh_thuc[i], van_bang_chung_chi=van_bang[i]))

    # Quá trình công tác
    qt_tu = f.getlist("qt_tu")
    qt_den = f.getlist("qt_den")
    qt_chuc_danh = f.getlist("qt_chuc_danh")
    QuaTrinhCongTac.query.filter_by(can_bo_id=cb.id).delete()
    for i in range(len(qt_tu)):
        if qt_chuc_danh[i].strip():
            db.session.add(QuaTrinhCongTac(
                can_bo_id=cb.id, tu_thang_nam=qt_tu[i], den_thang_nam=qt_den[i],
                chuc_danh_don_vi=qt_chuc_danh[i]))

    # Khen thưởng
    kt_noi_dung = f.getlist("kt_noi_dung")
    kt_nam = f.getlist("kt_nam")
    KhenThuong.query.filter_by(can_bo_id=cb.id).delete()
    for i in range(len(kt_noi_dung)):
        if kt_noi_dung[i].strip():
            db.session.add(KhenThuong(can_bo_id=cb.id, noi_dung=kt_noi_dung[i], nam=parse_int(kt_nam[i])))

    # Kỷ luật
    kl_hinh_thuc = f.getlist("kl_hinh_thuc")
    kl_cap_qd = f.getlist("kl_cap_qd")
    kl_ly_do = f.getlist("kl_ly_do")
    kl_nam = f.getlist("kl_nam")
    KyLuat.query.filter_by(can_bo_id=cb.id).delete()
    for i in range(len(kl_hinh_thuc)):
        if kl_hinh_thuc[i].strip():
            db.session.add(KyLuat(can_bo_id=cb.id, hinh_thuc=kl_hinh_thuc[i], cap_quyet_dinh=kl_cap_qd[i],
                                   ly_do=kl_ly_do[i], nam=parse_int(kl_nam[i])))

    # Đặc điểm lịch sử bản thân
    ls_bat_tu = f.get("ls_bat_tu", "").strip()
    ls_che_do_cu = f.get("ls_che_do_cu", "").strip()
    LichSuBanThan.query.filter_by(can_bo_id=cb.id).delete()
    if ls_bat_tu:
        db.session.add(LichSuBanThan(can_bo_id=cb.id, loai="Bị bắt/bị tù", noi_dung=ls_bat_tu))
    if ls_che_do_cu:
        db.session.add(LichSuBanThan(can_bo_id=cb.id, loai="Làm việc chế độ cũ", noi_dung=ls_che_do_cu))

    # Quan hệ nước ngoài
    qhnn_to_chuc = f.get("qhnn_to_chuc", "").strip()
    qhnn_than_nhan = f.get("qhnn_than_nhan", "").strip()
    QuanHeNuocNgoai.query.filter_by(can_bo_id=cb.id).delete()
    if qhnn_to_chuc:
        db.session.add(QuanHeNuocNgoai(can_bo_id=cb.id, loai="Tổ chức chính trị/kinh tế/xã hội", noi_dung=qhnn_to_chuc))
    if qhnn_than_nhan:
        db.session.add(QuanHeNuocNgoai(can_bo_id=cb.id, loai="Thân nhân ở nước ngoài", noi_dung=qhnn_than_nhan))

    # Quan hệ gia đình
    gd_nhom = f.getlist("gd_nhom")
    gd_quan_he = f.getlist("gd_quan_he")
    gd_ho_ten = f.getlist("gd_ho_ten")
    gd_nam_sinh = f.getlist("gd_nam_sinh")
    gd_thong_tin = f.getlist("gd_thong_tin")
    QuanHeGiaDinh.query.filter_by(can_bo_id=cb.id).delete()
    for i in range(len(gd_ho_ten)):
        if gd_ho_ten[i].strip():
            db.session.add(QuanHeGiaDinh(
                can_bo_id=cb.id, nhom=gd_nhom[i], quan_he=gd_quan_he[i], ho_ten=gd_ho_ten[i],
                nam_sinh=parse_int(gd_nam_sinh[i]), thong_tin=gd_thong_tin[i]))

    # Hoàn cảnh kinh tế (1-1)
    HoanCanhKinhTe.query.filter_by(can_bo_id=cb.id).delete()
    hckt = HoanCanhKinhTe(
        can_bo_id=cb.id,
        nguon_thu_nhap_luong=f.get("hckt_nguon_luong"),
        nguon_thu_nhap_khac=f.get("hckt_nguon_khac"),
        nha_o_loai=f.get("hckt_nha_o_loai"),
        nha_o_dien_tich_m2=parse_decimal(f.get("hckt_nha_o_dien_tich")),
        dat_o_duoc_cap_m2=parse_decimal(f.get("hckt_dat_duoc_cap")),
        dat_o_tu_mua_m2=parse_decimal(f.get("hckt_dat_tu_mua")),
        dat_san_xuat_kinh_doanh=f.get("hckt_dat_san_xuat"),
    )
    db.session.add(hckt)


# ---------------------------------------------------------------- đơn vị
@app.route("/don-vi")
@login_required
def don_vi_list_page():
    ds = DonVi.query.order_by(DonVi.ten_don_vi).all()
    return render_template("donvi.html", ds=ds)


@app.route("/don-vi/moi", methods=["POST"])
@role_required("admin")
def don_vi_them():
    dv = DonVi(
        ma_don_vi=request.form.get("ma_don_vi"),
        ten_don_vi=request.form.get("ten_don_vi"),
        loai_don_vi=request.form.get("loai_don_vi"),
        don_vi_cha_id=parse_int(request.form.get("don_vi_cha_id")),
        dia_chi=request.form.get("dia_chi"),
    )
    db.session.add(dv)
    db.session.commit()
    flash("Đã thêm đơn vị.", "success")
    return redirect(url_for("don_vi_list_page"))


@app.route("/don-vi/<int:id>/xoa", methods=["POST"])
@role_required("admin")
def don_vi_xoa(id):
    dv = DonVi.query.get_or_404(id)
    if dv.can_bo_list:
        flash("Không thể xóa: đơn vị vẫn còn cán bộ trực thuộc.", "error")
    else:
        db.session.delete(dv)
        db.session.commit()
        flash("Đã xóa đơn vị.", "success")
    return redirect(url_for("don_vi_list_page"))


# ---------------------------------------------------------------- API tra cứu nhanh (JSON, cho tìm kiếm gợi ý)
@app.route("/api/tim-kiem")
@login_required
def api_tim_kiem():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    like = f"%{q}%"
    ds = CanBo.query.filter(or_(
        CanBo.ho_ten_khai_sinh.ilike(like),
        CanBo.so_hieu_can_bo.ilike(like),
    )).limit(10).all()
    return jsonify([{"id": c.id, "ten": c.ho_ten_khai_sinh, "chuc_vu": c.chuc_vu, "don_vi": c.don_vi.ten_don_vi if c.don_vi else ""} for c in ds])


# ---------------------------------------------------------------- khởi tạo CSDL + tài khoản mẫu
@app.cli.command("init-db")
def init_db():
    """flask --app app init-db"""
    db.create_all()
    if not TaiKhoan.query.filter_by(ten_dang_nhap="admin").first():
        tk = TaiKhoan(ten_dang_nhap="admin", ho_ten="Quản trị hệ thống", vai_tro="admin")
        tk.set_password("admin123")
        db.session.add(tk)
    if not DonVi.query.first():
        so = DonVi(ma_don_vi="SNNMT", ten_don_vi="Sở Nông nghiệp và Môi trường", loai_don_vi="Sở")
        db.session.add(so)
        db.session.flush()
        for ma, ten, loai in [
            ("VP", "Văn phòng Sở", "Phòng"),
            ("TCCB", "Phòng Tổ chức cán bộ", "Phòng"),
            ("CCTL", "Chi cục Thủy lợi", "Chi cục"),
            ("CCMT", "Chi cục Bảo vệ Môi trường", "Chi cục"),
            ("CCKL", "Chi cục Kiểm lâm", "Chi cục"),
        ]:
            db.session.add(DonVi(ma_don_vi=ma, ten_don_vi=ten, loai_don_vi=loai, don_vi_cha_id=so.id))
    db.session.commit()
    print("Đã khởi tạo CSDL và tài khoản admin/admin123")


with app.app_context():
    db.create_all()
    if not TaiKhoan.query.filter_by(ten_dang_nhap="admin").first():
        tk = TaiKhoan(ten_dang_nhap="admin", ho_ten="Quản trị hệ thống", vai_tro="admin")
        tk.set_password("admin123")
        db.session.add(tk)
        db.session.commit()
    if not DonVi.query.first():
        so = DonVi(ma_don_vi="SNNMT", ten_don_vi="Sở Nông nghiệp và Môi trường", loai_don_vi="Sở")
        db.session.add(so)
        db.session.flush()
        for ma, ten, loai in [
            ("VP", "Văn phòng Sở", "Phòng"),
            ("TCCB", "Phòng Tổ chức cán bộ", "Phòng"),
            ("CCTL", "Chi cục Thủy lợi", "Chi cục"),
            ("CCMT", "Chi cục Bảo vệ Môi trường", "Chi cục"),
            ("CCKL", "Chi cục Kiểm lâm", "Chi cục"),
        ]:
            db.session.add(DonVi(ma_don_vi=ma, ten_don_vi=ten, loai_don_vi=loai, don_vi_cha_id=so.id))
        db.session.commit()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
