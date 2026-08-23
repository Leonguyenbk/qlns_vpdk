import os
from datetime import datetime, date
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from sqlalchemy import or_

from models import (
    db, DonVi, CanBo, ChucVu, DaoTao, QuaTrinhCongTac, QuaTrinhLuong,
    KhenThuong, KyLuat, LichSuBanThan, QuanHeNuocNgoai, QuanHeGiaDinh,
    HoanCanhKinhTe, TaiKhoan
)
from docx_export import tao_docx_so_yeu_ly_lich

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]

db.init_app(app)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
jwt = JWTManager(app)


# ---------------------------------------------------------------- helpers
def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if get_jwt().get("vai_tro") not in roles:
                return jsonify({"error": "Không đủ quyền thực hiện thao tác này"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------- auth
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("ten_dang_nhap", "").strip()
    password = data.get("mat_khau", "")

    tk = TaiKhoan.query.filter_by(ten_dang_nhap=username).first()
    if not tk or not tk.check_password(password):
        return jsonify({"error": "Sai tên đăng nhập hoặc mật khẩu"}), 401

    token = create_access_token(
        identity=str(tk.id),
        additional_claims={"vai_tro": tk.vai_tro, "ho_ten": tk.ho_ten},
    )
    return jsonify({"access_token": token, "user": tk.to_dict()})


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    claims = get_jwt()
    return jsonify({
        "id": get_jwt_identity(),
        "ho_ten": claims.get("ho_ten"),
        "vai_tro": claims.get("vai_tro"),
    })


# ---------------------------------------------------------------- đơn vị
@app.route("/api/don-vi", methods=["GET"])
@jwt_required()
def don_vi_list():
    ds = DonVi.query.order_by(DonVi.ten_don_vi).all()
    return jsonify([d.to_dict() for d in ds])


@app.route("/api/don-vi/<int:id>", methods=["GET"])
@jwt_required()
def don_vi_get(id):
    dv = DonVi.query.get_or_404(id)
    return jsonify(dv.to_dict())


@app.route("/api/don-vi", methods=["POST"])
@role_required("admin")
def don_vi_create():
    data = request.get_json(silent=True) or {}
    if not data.get("ma_don_vi") or not data.get("ten_don_vi"):
        return jsonify({"error": "Thiếu mã đơn vị hoặc tên đơn vị"}), 400

    dv = DonVi(
        ma_don_vi=data.get("ma_don_vi"),
        ten_don_vi=data.get("ten_don_vi"),
        loai_don_vi=data.get("loai_don_vi"),
        don_vi_cha_id=data.get("don_vi_cha_id"),
        dia_chi=data.get("dia_chi"),
        ghi_chu=data.get("ghi_chu"),
    )
    db.session.add(dv)
    db.session.commit()
    return jsonify(dv.to_dict()), 201


@app.route("/api/don-vi/<int:id>", methods=["PUT"])
@role_required("admin")
def don_vi_update(id):
    dv = DonVi.query.get_or_404(id)
    data = request.get_json(silent=True) or {}
    for field in ["ma_don_vi", "ten_don_vi", "loai_don_vi", "don_vi_cha_id", "dia_chi", "ghi_chu"]:
        if field in data:
            setattr(dv, field, data[field])
    db.session.commit()
    return jsonify(dv.to_dict())


@app.route("/api/don-vi/<int:id>", methods=["DELETE"])
@role_required("admin")
def don_vi_delete(id):
    dv = DonVi.query.get_or_404(id)
    if dv.can_bo_list:
        return jsonify({"error": "Đơn vị còn cán bộ trực thuộc, không thể xóa"}), 400
    db.session.delete(dv)
    db.session.commit()
    return "", 204


# ---------------------------------------------------------------- cán bộ - danh sách/tra cứu
@app.route("/api/can-bo", methods=["GET"])
@jwt_required()
def can_bo_list():
    q = request.args.get("q", "").strip()
    don_vi_id = request.args.get("don_vi_id", type=int)
    chuc_vu_id = request.args.get("chuc_vu_id", type=int)
    trang_thai = request.args.get("trang_thai", "").strip()

    query = CanBo.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            CanBo.ho_ten_khai_sinh.ilike(like),
            CanBo.so_hieu_can_bo.ilike(like),
            CanBo.so_cmnd_cccd.ilike(like),
        ))
    if don_vi_id:
        query = query.filter(CanBo.don_vi_id == don_vi_id)
    if chuc_vu_id:
        query = query.filter(CanBo.chuc_vu_id == chuc_vu_id)
    if trang_thai:
        query = query.filter(CanBo.trang_thai == trang_thai)

    ds = query.order_by(CanBo.ho_ten_khai_sinh).all()
    return jsonify([c.to_dict() for c in ds])


@app.route("/api/can-bo/<int:id>", methods=["GET"])
@jwt_required()
def can_bo_detail(id):
    cb = CanBo.query.get_or_404(id)
    return jsonify(cb.to_dict(full=True))


@app.route("/api/can-bo", methods=["POST"])
@role_required("admin", "editor")
def can_bo_create():
    data = request.get_json(silent=True) or {}
    if not data.get("ho_ten_khai_sinh"):
        return jsonify({"error": "Thiếu họ và tên khai sinh"}), 400

    cb = CanBo()
    _apply_can_bo_data(cb, data)
    db.session.commit()
    return jsonify(cb.to_dict(full=True)), 201


@app.route("/api/can-bo/<int:id>", methods=["PUT"])
@role_required("admin", "editor")
def can_bo_update(id):
    cb = CanBo.query.get_or_404(id)
    data = request.get_json(silent=True) or {}
    _apply_can_bo_data(cb, data)
    db.session.commit()
    return jsonify(cb.to_dict(full=True))


@app.route("/api/can-bo/<int:id>", methods=["DELETE"])
@role_required("admin")
def can_bo_delete(id):
    cb = CanBo.query.get_or_404(id)
    db.session.delete(cb)
    db.session.commit()
    return "", 204


def parse_int(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def parse_decimal(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def clean_str(value):
    """Chuỗi rỗng '' -> None, giữ nguyên nếu có giá trị."""
    return value if value not in ("",) else None


def _apply_can_bo_data(cb, data):
    simple_fields = [
        "so_hieu_can_bo", "don_vi_id", "don_vi_co_so",
        "ho_ten_khai_sinh", "ten_goi_khac", "gioi_tinh", "anh_chan_dung",
        "noi_sinh", "que_quan_xa", "que_quan_huyen", "que_quan_tinh",
        "noi_o_hien_nay", "dien_thoai", "email",
        "dan_toc", "ton_giao", "thanh_phan_gia_dinh", "nghe_nghiep_truoc_tuyen_dung",
        "noi_tuyen_dung", "ngay_tham_gia_to_chuc_ct_xh", "quan_ham_chuc_vu_cao_nhat",
        "trinh_do_giao_duc_pho_thong", "hoc_ham_hoc_vi_cao_nhat", "ly_luan_chinh_tri", "ngoai_ngu",
        "cap_uy_hien_tai", "cap_uy_kiem", "chuc_vu", "phu_cap_chuc_vu",
        "cong_tac_chinh_dang_lam", "ngach_cong_chuc", "ma_so_ngach", "bac_luong",
        "luong_tu_thang_nam", "danh_hieu_duoc_phong", "so_truong_cong_tac", "cong_viec_lam_lau_nhat",
        "tinh_trang_suc_khoe", "nhom_mau", "so_cmnd_cccd", "thuong_binh_loai",
        "trang_thai",
    ]
    for field in simple_fields:
        if field in data:
            setattr(cb, field, clean_str(data[field]))

    # don_vi_id là khóa ngoại số nguyên, không phải chuỗi -> xử lý riêng
    if "don_vi_id" in data:
        cb.don_vi_id = parse_int(data["don_vi_id"])
    
    if "chuc_vu_id" in data:
        cb.chuc_vu_id = parse_int(data["chuc_vu_id"])

    date_fields = [
        "ngay_sinh", "ngay_tuyen_dung", "ngay_vao_co_quan_hien_tai", "ngay_tham_gia_cach_mang",
        "ngay_vao_dang", "ngay_chinh_thuc_dang", "ngay_nhap_ngu", "ngay_xuat_ngu",
    ]
    for field in date_fields:
        if field in data:
            setattr(cb, field, parse_date(data[field]))

    # --- các trường số: BẮT BUỘC qua parse_decimal, không gán thẳng ---
    if "he_so_luong" in data:
        cb.he_so_luong = parse_decimal(data["he_so_luong"])
    if "chieu_cao_cm" in data:
        cb.chieu_cao_cm = parse_decimal(data["chieu_cao_cm"])
    if "can_nang_kg" in data:
        cb.can_nang_kg = parse_decimal(data["can_nang_kg"])

    if "gia_dinh_liet_si" in data:
        cb.gia_dinh_liet_si = bool(data["gia_dinh_liet_si"])

    if cb.id is None:
        db.session.add(cb)
        db.session.flush()

    if "dao_tao" in data:
        DaoTao.query.filter_by(can_bo_id=cb.id).delete()
        for d in data["dao_tao"]:
            db.session.add(DaoTao(
                can_bo_id=cb.id,
                ten_truong=clean_str(d.get("ten_truong")),
                nganh_hoc=clean_str(d.get("nganh_hoc")),
                tu_nam=parse_int(d.get("tu_nam")),
                den_nam=parse_int(d.get("den_nam")),
                hinh_thuc_hoc=clean_str(d.get("hinh_thuc_hoc")),
                van_bang_chung_chi=clean_str(d.get("van_bang_chung_chi")),
            ))

    if "qua_trinh_cong_tac" in data:
        QuaTrinhCongTac.query.filter_by(can_bo_id=cb.id).delete()
        for q in data["qua_trinh_cong_tac"]:
            db.session.add(QuaTrinhCongTac(
                can_bo_id=cb.id,
                tu_thang_nam=clean_str(q.get("tu_thang_nam")),
                den_thang_nam=clean_str(q.get("den_thang_nam")),
                chuc_danh_don_vi=clean_str(q.get("chuc_danh_don_vi")),
            ))

    if "qua_trinh_luong" in data:
        QuaTrinhLuong.query.filter_by(can_bo_id=cb.id).delete()
        for q in data["qua_trinh_luong"]:
            db.session.add(QuaTrinhLuong(
                can_bo_id=cb.id,
                thang_nam=clean_str(q.get("thang_nam")),
                ngach_bac=clean_str(q.get("ngach_bac")),
                he_so_luong=parse_decimal(q.get("he_so_luong")),
            ))

    if "khen_thuong" in data:
        KhenThuong.query.filter_by(can_bo_id=cb.id).delete()
        for k in data["khen_thuong"]:
            db.session.add(KhenThuong(
                can_bo_id=cb.id,
                noi_dung=clean_str(k.get("noi_dung")),
                nam=parse_int(k.get("nam")),
            ))

    if "ky_luat" in data:
        KyLuat.query.filter_by(can_bo_id=cb.id).delete()
        for k in data["ky_luat"]:
            db.session.add(KyLuat(
                can_bo_id=cb.id,
                hinh_thuc=clean_str(k.get("hinh_thuc")),
                cap_quyet_dinh=clean_str(k.get("cap_quyet_dinh")),
                ly_do=clean_str(k.get("ly_do")),
                nam=parse_int(k.get("nam")),
            ))

    if "lich_su_ban_than" in data:
        LichSuBanThan.query.filter_by(can_bo_id=cb.id).delete()
        for l in data["lich_su_ban_than"]:
            db.session.add(LichSuBanThan(
                can_bo_id=cb.id, loai=clean_str(l.get("loai")), noi_dung=clean_str(l.get("noi_dung"))
            ))

    if "quan_he_nuoc_ngoai" in data:
        QuanHeNuocNgoai.query.filter_by(can_bo_id=cb.id).delete()
        for q in data["quan_he_nuoc_ngoai"]:
            db.session.add(QuanHeNuocNgoai(
                can_bo_id=cb.id, loai=clean_str(q.get("loai")), noi_dung=clean_str(q.get("noi_dung"))
            ))

    if "quan_he_gia_dinh" in data:
        QuanHeGiaDinh.query.filter_by(can_bo_id=cb.id).delete()
        for g in data["quan_he_gia_dinh"]:
            db.session.add(QuanHeGiaDinh(
                can_bo_id=cb.id,
                nhom=clean_str(g.get("nhom")),
                quan_he=clean_str(g.get("quan_he")),
                ho_ten=clean_str(g.get("ho_ten")),
                nam_sinh=parse_int(g.get("nam_sinh")),
                thong_tin=clean_str(g.get("thong_tin")),
            ))

    if "hoan_canh_kinh_te" in data:
        HoanCanhKinhTe.query.filter_by(can_bo_id=cb.id).delete()
        h = data["hoan_canh_kinh_te"] or {}
        db.session.add(HoanCanhKinhTe(
            can_bo_id=cb.id,
            nguon_thu_nhap_luong=clean_str(h.get("nguon_thu_nhap_luong")),
            nguon_thu_nhap_khac=clean_str(h.get("nguon_thu_nhap_khac")),
            nha_o_loai=clean_str(h.get("nha_o_loai")),
            nha_o_dien_tich_m2=parse_decimal(h.get("nha_o_dien_tich_m2")),
            dat_o_duoc_cap_m2=parse_decimal(h.get("dat_o_duoc_cap_m2")),
            dat_o_tu_mua_m2=parse_decimal(h.get("dat_o_tu_mua_m2")),
            dat_san_xuat_kinh_doanh=clean_str(h.get("dat_san_xuat_kinh_doanh")),
        ))

@app.route("/api/chuc-vu", methods=["GET"])
@jwt_required()
def chuc_vu_list():
    ds = ChucVu.query.order_by(ChucVu.cap_bac).all()
    return jsonify([c.to_dict() for c in ds])


@app.route("/api/chuc-vu", methods=["POST"])
@role_required("admin")
def chuc_vu_create():
    data = request.get_json(silent=True) or {}
    if not data.get("ten_chuc_vu") or data.get("cap_bac") is None:
        return jsonify({"error": "Thiếu tên chức vụ hoặc cấp bậc"}), 400
    cv = ChucVu(
        ten_chuc_vu=data["ten_chuc_vu"],
        cap_bac=parse_int(data["cap_bac"]),
        mo_ta=clean_str(data.get("mo_ta")),
    )
    db.session.add(cv)
    db.session.commit()
    return jsonify(cv.to_dict()), 201


@app.route("/api/chuc-vu/<int:id>", methods=["PUT"])
@role_required("admin")
def chuc_vu_update(id):
    cv = ChucVu.query.get_or_404(id)
    data = request.get_json(silent=True) or {}
    if "ten_chuc_vu" in data:
        cv.ten_chuc_vu = data["ten_chuc_vu"]
    if "cap_bac" in data:
        cv.cap_bac = parse_int(data["cap_bac"])
    if "mo_ta" in data:
        cv.mo_ta = clean_str(data["mo_ta"])
    db.session.commit()
    return jsonify(cv.to_dict())


@app.route("/api/chuc-vu/<int:id>", methods=["DELETE"])
@role_required("admin")
def chuc_vu_delete(id):
    cv = ChucVu.query.get_or_404(id)
    if cv.can_bo_list:
        return jsonify({"error": "Còn cán bộ đang giữ chức vụ này, không thể xóa"}), 400
    db.session.delete(cv)
    db.session.commit()
    return "", 204

@app.route("/api/can-bo/<int:id>/xuat-docx", methods=["GET"])
@jwt_required()
def can_bo_xuat_docx(id):
    cb = CanBo.query.get_or_404(id)
    buffer = tao_docx_so_yeu_ly_lich(cb)
    ten_file = f"So_yeu_ly_lich_{cb.ho_ten_khai_sinh.replace(' ', '_')}.docx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=ten_file,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

# ---------------------------------------------------------------- khởi tạo CSDL + tài khoản/đơn vị mẫu
@app.cli.command("init-db")
def init_db():
    """Chạy: flask --app app init-db"""
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
    print("Đã khởi tạo CSDL, tài khoản admin/admin123 và đơn vị mẫu.")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=5000)