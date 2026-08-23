import os
from datetime import datetime, date
from functools import wraps
from urllib.parse import parse_qsl, urlsplit

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import URL

from models import (
    db, DonVi, CanBo, ChucVu, GioiHanChucVuDonVi, DaoTao, QuaTrinhCongTac, QuaTrinhLuong,
    KhenThuong, KyLuat, LichSuBanThan, QuanHeNuocNgoai, QuanHeGiaDinh,
    HoanCanhKinhTe, TaiKhoan
)
from docx_export import tao_docx_so_yeu_ly_lich

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
database_parts = urlsplit(os.environ["DATABASE_URL"])
app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
    database_parts.scheme,
    username=database_parts.username,
    password=database_parts.password,
    host=database_parts.hostname,
    port=database_parts.port,
    database=database_parts.path.lstrip("/"),
    query=dict(parse_qsl(database_parts.query)),
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]

db.init_app(app)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
jwt = JWTManager(app)


# ---------------------------------------------------------------- helpers
def parse_date(value):
    if not value:
        return None


def normalize_code(value):
    return value.strip().upper() if isinstance(value, str) else ""


def required_text(value):
    return value.strip() if isinstance(value, str) else ""


def bad_request(message, field=None):
    payload = {"error": message}
    if field:
        payload["field"] = field
    return jsonify(payload), 400


def validate_parent(dv, parent_id):
    if parent_id is None:
        return None
    if parent_id == dv.id:
        return "Đơn vị không thể chọn chính nó làm đơn vị cấp trên."
    parent = db.session.get(DonVi, parent_id)
    if not parent:
        return "Đơn vị cấp trên không tồn tại."
    seen = {dv.id}
    while parent:
        if parent.id in seen:
            return "Quan hệ đơn vị cha–con không được tạo vòng lặp."
        seen.add(parent.id)
        parent = parent.cha
    return None


def current_position_count(don_vi_id, chuc_vu_id):
    return db.session.query(func.count(CanBo.id)).filter(
        CanBo.don_vi_id == don_vi_id,
        CanBo.chuc_vu_id == chuc_vu_id,
        CanBo.trang_thai == "Đang công tác",
    ).scalar() or 0


def validate_position_limit(don_vi_id, chuc_vu_id):
    if not don_vi_id or not chuc_vu_id:
        return None
    limit = GioiHanChucVuDonVi.query.filter_by(
        don_vi_id=don_vi_id, chuc_vu_id=chuc_vu_id
    ).with_for_update().first()
    if limit and current_position_count(don_vi_id, chuc_vu_id) > limit.so_luong_toi_da:
        don_vi = db.session.get(DonVi, don_vi_id)
        chuc_vu = db.session.get(ChucVu, chuc_vu_id)
        return (
            f"{don_vi.ten_don_vi} đã đủ {limit.so_luong_toi_da:02d} "
            f"{chuc_vu.ten_chuc_vu}."
        )
    return None


def validate_assignment_limit(cb, same_assignment=False):
    limit = GioiHanChucVuDonVi.query.filter_by(
        don_vi_id=cb.don_vi_id, chuc_vu_id=cb.chuc_vu_id
    ).with_for_update().first()
    if not limit or cb.trang_thai != "Đang công tác" or same_assignment:
        return None
    count_query = db.session.query(func.count(CanBo.id)).filter(
        CanBo.don_vi_id == cb.don_vi_id,
        CanBo.chuc_vu_id == cb.chuc_vu_id,
        CanBo.trang_thai == "Đang công tác",
    )
    if cb.id:
        count_query = count_query.filter(CanBo.id != cb.id)
    count = count_query.scalar() or 0
    if count >= limit.so_luong_toi_da:
        don_vi = db.session.get(DonVi, cb.don_vi_id)
        chuc_vu = db.session.get(ChucVu, cb.chuc_vu_id)
        return (
            f"{don_vi.ten_don_vi} đã đủ {limit.so_luong_toi_da:02d} "
            f"{chuc_vu.ten_chuc_vu}."
        )
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
    query = DonVi.query
    q = required_text(request.args.get("q"))
    loai = required_text(request.args.get("loai_don_vi"))
    parent_id = request.args.get("don_vi_cha_id", type=int)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(DonVi.ma_don_vi.ilike(like), DonVi.ten_don_vi.ilike(like)))
    if loai:
        query = query.filter(DonVi.loai_don_vi == loai)
    if parent_id:
        query = query.filter(DonVi.don_vi_cha_id == parent_id)
    ds = query.order_by(DonVi.ten_don_vi).all()
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
    ma_don_vi = normalize_code(data.get("ma_don_vi"))
    ten_don_vi = required_text(data.get("ten_don_vi"))
    if not ma_don_vi:
        return bad_request("Mã đơn vị là bắt buộc.", "ma_don_vi")
    if not ten_don_vi:
        return bad_request("Tên đơn vị là bắt buộc.", "ten_don_vi")
    if DonVi.query.filter_by(ma_don_vi=ma_don_vi).first():
        return bad_request("Mã đơn vị đã tồn tại.", "ma_don_vi")
    parent_id = parse_int(data.get("don_vi_cha_id"))
    parent_error = validate_parent(DonVi(), parent_id)
    if parent_error:
        return bad_request(parent_error, "don_vi_cha_id")

    dv = DonVi(
        ma_don_vi=ma_don_vi,
        ten_don_vi=ten_don_vi,
        loai_don_vi=data.get("loai_don_vi"),
        don_vi_cha_id=parent_id,
        dia_chi=data.get("dia_chi"),
        ghi_chu=data.get("ghi_chu"),
    )
    db.session.add(dv)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return bad_request("Mã đơn vị đã tồn tại.", "ma_don_vi")
    return jsonify(dv.to_dict()), 201


@app.route("/api/don-vi/<int:id>", methods=["PUT"])
@role_required("admin")
def don_vi_update(id):
    dv = DonVi.query.get_or_404(id)
    data = request.get_json(silent=True) or {}
    if "ma_don_vi" in data:
        ma_don_vi = normalize_code(data["ma_don_vi"])
        if not ma_don_vi:
            return bad_request("Mã đơn vị là bắt buộc.", "ma_don_vi")
        duplicate = DonVi.query.filter(DonVi.ma_don_vi == ma_don_vi, DonVi.id != id).first()
        if duplicate:
            return bad_request("Mã đơn vị đã tồn tại.", "ma_don_vi")
        dv.ma_don_vi = ma_don_vi
    if "ten_don_vi" in data:
        dv.ten_don_vi = required_text(data["ten_don_vi"])
        if not dv.ten_don_vi:
            return bad_request("Tên đơn vị là bắt buộc.", "ten_don_vi")
    if "don_vi_cha_id" in data:
        parent_id = parse_int(data["don_vi_cha_id"])
        parent_error = validate_parent(dv, parent_id)
        if parent_error:
            return bad_request(parent_error, "don_vi_cha_id")
        dv.don_vi_cha_id = parent_id
    for field in ["loai_don_vi", "dia_chi", "ghi_chu"]:
        if field in data:
            setattr(dv, field, data[field])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return bad_request("Mã đơn vị đã tồn tại.", "ma_don_vi")
    return jsonify(dv.to_dict())


@app.route("/api/don-vi/<int:id>", methods=["DELETE"])
@role_required("admin")
def don_vi_delete(id):
    dv = DonVi.query.get_or_404(id)
    if dv.can_bo_list:
        return jsonify({"error": "Đơn vị còn cán bộ trực thuộc, không thể xóa"}), 400
    if dv.con:
        return jsonify({"error": "Đơn vị còn đơn vị trực thuộc, không thể xóa"}), 400
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
    error = validate_assignment_limit(cb)
    if error:
        db.session.rollback()
        return bad_request(error)
    db.session.commit()
    return jsonify(cb.to_dict(full=True)), 201


@app.route("/api/can-bo/<int:id>", methods=["PUT"])
@role_required("admin", "editor")
def can_bo_update(id):
    cb = CanBo.query.get_or_404(id)
    data = request.get_json(silent=True) or {}
    old_assignment = (cb.don_vi_id, cb.chuc_vu_id, cb.trang_thai)
    _apply_can_bo_data(cb, data)
    error = validate_assignment_limit(cb, old_assignment == (cb.don_vi_id, cb.chuc_vu_id, cb.trang_thai))
    if error:
        db.session.rollback()
        return bad_request(error)
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
    query = ChucVu.query
    q = required_text(request.args.get("q"))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(ChucVu.ma_chuc_vu.ilike(like), ChucVu.ten_chuc_vu.ilike(like)))
    if request.args.get("cap_bac"):
        cap_bac = parse_int(request.args.get("cap_bac"))
        if cap_bac is not None:
            query = query.filter(ChucVu.cap_bac == cap_bac)
    ds = query.order_by(ChucVu.cap_bac, ChucVu.ten_chuc_vu).all()
    return jsonify([c.to_dict() for c in ds])


@app.route("/api/chuc-vu/<int:id>", methods=["GET"])
@jwt_required()
def chuc_vu_get(id):
    return jsonify(ChucVu.query.get_or_404(id).to_dict())


@app.route("/api/chuc-vu/chua-co-ma", methods=["GET"])
@jwt_required()
def chuc_vu_without_code():
    ds = ChucVu.query.filter(
        or_(ChucVu.ma_chuc_vu.is_(None), ChucVu.ma_chuc_vu == "")
    ).order_by(ChucVu.cap_bac, ChucVu.ten_chuc_vu).all()
    return jsonify([c.to_dict() for c in ds])


@app.route("/api/chuc-vu", methods=["POST"])
@role_required("admin")
def chuc_vu_create():
    data = request.get_json(silent=True) or {}
    ma_chuc_vu = normalize_code(data.get("ma_chuc_vu"))
    ten_chuc_vu = required_text(data.get("ten_chuc_vu"))
    cap_bac = parse_int(data.get("cap_bac"))
    if not ma_chuc_vu:
        return bad_request("Mã chức vụ là bắt buộc khi tạo mới.", "ma_chuc_vu")
    if not ten_chuc_vu:
        return bad_request("Tên chức vụ là bắt buộc.", "ten_chuc_vu")
    if cap_bac is None:
        return bad_request("Cấp bậc phải là số nguyên hợp lệ.", "cap_bac")
    if ChucVu.query.filter_by(ma_chuc_vu=ma_chuc_vu).first():
        return bad_request("Mã chức vụ đã tồn tại.", "ma_chuc_vu")
    cv = ChucVu(
        ma_chuc_vu=ma_chuc_vu,
        ten_chuc_vu=ten_chuc_vu,
        cap_bac=cap_bac,
        mo_ta=clean_str(data.get("mo_ta")),
    )
    db.session.add(cv)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return bad_request("Mã chức vụ đã tồn tại.", "ma_chuc_vu")
    return jsonify(cv.to_dict()), 201


@app.route("/api/chuc-vu/<int:id>", methods=["PUT"])
@role_required("admin")
def chuc_vu_update(id):
    cv = ChucVu.query.get_or_404(id)
    data = request.get_json(silent=True) or {}
    if "ma_chuc_vu" in data:
        ma_chuc_vu = normalize_code(data["ma_chuc_vu"])
        if not ma_chuc_vu:
            return bad_request("Mã chức vụ không được để trống khi cập nhật.", "ma_chuc_vu")
        duplicate = ChucVu.query.filter(ChucVu.ma_chuc_vu == ma_chuc_vu, ChucVu.id != id).first()
        if duplicate:
            return bad_request("Mã chức vụ đã tồn tại.", "ma_chuc_vu")
        cv.ma_chuc_vu = ma_chuc_vu
    if "ten_chuc_vu" in data:
        cv.ten_chuc_vu = required_text(data["ten_chuc_vu"])
        if not cv.ten_chuc_vu:
            return bad_request("Tên chức vụ là bắt buộc.", "ten_chuc_vu")
    if "cap_bac" in data:
        cv.cap_bac = parse_int(data["cap_bac"])
        if cv.cap_bac is None:
            return bad_request("Cấp bậc phải là số nguyên hợp lệ.", "cap_bac")
    if "mo_ta" in data:
        cv.mo_ta = clean_str(data["mo_ta"])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return bad_request("Mã chức vụ đã tồn tại.", "ma_chuc_vu")
    return jsonify(cv.to_dict())


@app.route("/api/chuc-vu/<int:id>", methods=["DELETE"])
@role_required("admin")
def chuc_vu_delete(id):
    cv = ChucVu.query.get_or_404(id)
    if cv.can_bo_list:
        return jsonify({"error": "Còn cán bộ đang giữ chức vụ này, không thể xóa"}), 400
    if cv.gioi_han_don_vi_list:
        return jsonify({"error": "Chức vụ đang có cấu hình giới hạn tại đơn vị, không thể xóa"}), 400
    db.session.delete(cv)
    db.session.commit()
    return "", 204


# ---------------------------------------------------------------- giới hạn chức vụ theo đơn vị
def position_limit_to_dict(limit):
    current = current_position_count(limit.don_vi_id, limit.chuc_vu_id)
    remaining = max(limit.so_luong_toi_da - current, 0)
    return {
        "id": limit.id,
        "don_vi_id": limit.don_vi_id,
        "ma_don_vi": limit.don_vi.ma_don_vi,
        "ten_don_vi": limit.don_vi.ten_don_vi,
        "chuc_vu_id": limit.chuc_vu_id,
        "ma_chuc_vu": limit.chuc_vu.ma_chuc_vu,
        "ten_chuc_vu": limit.chuc_vu.ten_chuc_vu,
        "so_luong_toi_da": limit.so_luong_toi_da,
        "so_luong_hien_tai": current,
        "so_luong_con_lai": remaining,
        "da_dat_gioi_han": current >= limit.so_luong_toi_da,
        "vuot_gioi_han": current > limit.so_luong_toi_da,
        "ghi_chu": limit.ghi_chu,
    }


@app.route("/api/gioi-han-chuc-vu-don-vi", methods=["GET"])
@jwt_required()
def position_limit_list():
    query = GioiHanChucVuDonVi.query.join(DonVi).join(ChucVu)
    q = required_text(request.args.get("q"))
    don_vi_id = request.args.get("don_vi_id", type=int)
    chuc_vu_id = request.args.get("chuc_vu_id", type=int)
    status = required_text(request.args.get("trang_thai"))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(DonVi.ma_don_vi.ilike(like), DonVi.ten_don_vi.ilike(like),
                                 ChucVu.ma_chuc_vu.ilike(like), ChucVu.ten_chuc_vu.ilike(like)))
    if don_vi_id:
        query = query.filter(GioiHanChucVuDonVi.don_vi_id == don_vi_id)
    if chuc_vu_id:
        query = query.filter(GioiHanChucVuDonVi.chuc_vu_id == chuc_vu_id)
    result = [position_limit_to_dict(limit) for limit in query.order_by(DonVi.ten_don_vi, ChucVu.cap_bac).all()]
    if status == "con_vi_tri":
        result = [item for item in result if not item["da_dat_gioi_han"]]
    elif status == "da_du":
        result = [item for item in result if item["da_dat_gioi_han"] and not item["vuot_gioi_han"]]
    elif status == "vuot":
        result = [item for item in result if item["vuot_gioi_han"]]
    return jsonify(result)


@app.route("/api/gioi-han-chuc-vu-don-vi/<int:id>", methods=["GET"])
@jwt_required()
def position_limit_get(id):
    return jsonify(position_limit_to_dict(GioiHanChucVuDonVi.query.get_or_404(id)))


def parse_position_limit(data, existing=None):
    don_vi_id = parse_int(data.get("don_vi_id"))
    chuc_vu_id = parse_int(data.get("chuc_vu_id"))
    maximum = parse_int(data.get("so_luong_toi_da"))
    if not don_vi_id:
        return None, "Đơn vị là bắt buộc.", "don_vi_id"
    if not chuc_vu_id:
        return None, "Chức vụ là bắt buộc.", "chuc_vu_id"
    if not db.session.get(DonVi, don_vi_id):
        return None, "Đơn vị không tồn tại.", "don_vi_id"
    if not db.session.get(ChucVu, chuc_vu_id):
        return None, "Chức vụ không tồn tại.", "chuc_vu_id"
    if maximum is None or maximum < 1:
        return None, "Số lượng tối đa phải là số nguyên từ 1 trở lên.", "so_luong_toi_da"
    current = current_position_count(don_vi_id, chuc_vu_id)
    if maximum < current:
        return None, f"Không thể đặt giới hạn thấp hơn số hiện tại ({current}).", "so_luong_toi_da"
    values = {
        "don_vi_id": don_vi_id, "chuc_vu_id": chuc_vu_id,
        "so_luong_toi_da": maximum, "ghi_chu": clean_str(data.get("ghi_chu")),
    }
    return values, None, None


@app.route("/api/gioi-han-chuc-vu-don-vi", methods=["POST"])
@role_required("admin")
def position_limit_create():
    values, error, field = parse_position_limit(request.get_json(silent=True) or {})
    if error:
        return bad_request(error, field)
    if GioiHanChucVuDonVi.query.filter_by(
        don_vi_id=values["don_vi_id"], chuc_vu_id=values["chuc_vu_id"]
    ).first():
        return bad_request("Cặp đơn vị và chức vụ này đã có cấu hình.")
    limit = GioiHanChucVuDonVi(**values)
    db.session.add(limit)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return bad_request("Cặp đơn vị và chức vụ này đã có cấu hình.")
    return jsonify(position_limit_to_dict(limit)), 201


@app.route("/api/gioi-han-chuc-vu-don-vi/<int:id>", methods=["PUT"])
@role_required("admin")
def position_limit_update(id):
    limit = GioiHanChucVuDonVi.query.get_or_404(id)
    GioiHanChucVuDonVi.query.filter_by(id=id).with_for_update().first()
    values, error, field = parse_position_limit(request.get_json(silent=True) or {}, limit)
    if error:
        return bad_request(error, field)
    duplicate = GioiHanChucVuDonVi.query.filter(
        GioiHanChucVuDonVi.don_vi_id == values["don_vi_id"],
        GioiHanChucVuDonVi.chuc_vu_id == values["chuc_vu_id"],
        GioiHanChucVuDonVi.id != id,
    ).first()
    if duplicate:
        return bad_request("Cặp đơn vị và chức vụ này đã có cấu hình.")
    for field_name, value in values.items():
        setattr(limit, field_name, value)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return bad_request("Cặp đơn vị và chức vụ này đã có cấu hình.")
    return jsonify(position_limit_to_dict(limit))


@app.route("/api/gioi-han-chuc-vu-don-vi/<int:id>", methods=["DELETE"])
@role_required("admin")
def position_limit_delete(id):
    limit = GioiHanChucVuDonVi.query.get_or_404(id)
    db.session.delete(limit)
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)