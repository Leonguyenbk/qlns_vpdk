# NOTE: Blueprint API của hệ gọi số (goiso), chuyển từ goiso_kios/server/app.py.
# Giữ nguyên mọi đường dẫn /api/* cũ (kiosk vật lý + frontend đều phụ thuộc).
# Các route render trang (Jinja) đã bỏ hết — giao diện nay ở frontend/src/pages/goiso/.
"""API bốc số / gọi số ĐA CHI NHÁNH + SSE realtime (JSON thuần, không render trang).

Mỗi chi nhánh có mã `code` (vd 'bmt'): mọi API ở /api/b/<code>/..., quản trị ở
/api/admin/...; giao diện tương ứng là frontend/src/pages/goiso/*.jsx (route
/b/<code>/counter|display|cho|man-hinh) và frontend/src/pages/admin/ (route /admin).
"""
import functools
import hashlib
import json
import os
import queue as queuelib
import sqlite3  # noqa: F401 (giữ cho tương thích)
from sqlalchemy.exc import OperationalError as _SAOperationalError
import threading
import time

from flask import Blueprint, Response, g, jsonify, redirect, request, stream_with_context

from . import legacy_db as db
from . import queue_logic as ql
from . import booking_logic as bk
from . import tts as tts_engine

bp = Blueprint("goiso", __name__)

DEBUG = bool(os.environ.get("GOISO_DEBUG"))
BASE_URL = os.environ.get("GOISO_BASE_URL", "").rstrip("/")
TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "")


def _server_version():
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, "VERSION"), os.path.join(here, "..", "VERSION")):
        try:
            with open(p, encoding="utf-8") as f:
                v = f.read().strip()
            if v:
                return v
        except OSError:
            continue
    return "0.0.0"


SERVER_VERSION = _server_version()


def _client_ip():
    return (request.headers.get("CF-Connecting-IP")
            or (request.headers.get("X-Forwarded-For", "").split(",")[0].strip())
            or request.remote_addr or "")

# db.init_db() được gọi từ app.modules.goiso.configure_goiso() sau khi .env đã nạp
# (tránh tạo file SQLite lạc chỗ khi import lúc chạy test).

# ----------------------------------------------------------------- SSE hub (theo chi nhánh)
_subscribers = {}  # branch_id -> set[Queue]
_sub_lock = threading.Lock()


def broadcast(branch_id, event: dict):
    data = json.dumps(event, ensure_ascii=False)
    with _sub_lock:
        subs = _subscribers.get(branch_id)
        if not subs:
            return
        dead = []
        for q in subs:
            try:
                q.put_nowait(data)
            except queuelib.Full:
                dead.append(q)
        for q in dead:
            subs.discard(q)


def push_snapshot(branch_id):
    broadcast(branch_id, ql.snapshot(branch_id))


# ----------------------------------------------------------------- decorators
def resolve_branch(view):
    @functools.wraps(view)
    def wrapper(code, *args, **kwargs):
        branch = db.get_branch(code)
        if not branch or not branch["active"]:
            if request.path.startswith("/api/"):
                return jsonify(error="Chi nhánh không tồn tại hoặc đã ngừng hoạt động."), 404
            return "Chi nhánh không tồn tại.", 404
        g.branch = branch
        return view(*args, **kwargs)
    return wrapper


def require_branch_key(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if not DEBUG:
            sent = request.headers.get("X-Branch-Key", "")
            import secrets as _s
            if not sent or not _s.compare_digest(sent, g.branch["api_key"]):
                return jsonify(error="Sai hoặc thiếu khoá chi nhánh (X-Branch-Key)."), 401
        return view(*args, **kwargs)
    return wrapper


def current_user():
    # Đăng nhập CHUNG: chỉ dùng JWT platform (cookie hoặc header).
    from .identity import current_platform_user_as_goiso

    return current_platform_user_as_goiso()


def _is_goiso_admin(u):
    return u["role"] == "admin" or "goiso.admin" in (u.get("perms") or ())


def _can_work_counter(u):
    """Phải là quản trị goiso hoặc có quyền goiso.counter."""
    return _is_goiso_admin(u) or "goiso.counter" in (u.get("perms") or ())


def _need_login_response(msg="Cần đăng nhập."):
    if request.path.startswith("/api/"):
        return jsonify(error=msg), 401
    from urllib.parse import quote

    nxt = request.full_path.rstrip("?") or request.path
    return redirect(f"/login?next={quote(nxt, safe='')}")


def login_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return _need_login_response()
        g.user = u
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return _need_login_response("Chưa đăng nhập quản trị.")
        if not _is_goiso_admin(u):
            if request.path.startswith("/api/"):
                return jsonify(error="Chỉ quản trị viên gọi số (goiso.admin)."), 403
            return "Chỉ quản trị viên mới truy cập được trang này.", 403
        g.user = u
        return view(*args, **kwargs)
    return wrapper


def counter_guard(view):
    """Yêu cầu đăng nhập + quyền trực quầy; nhân viên chỉ thao tác trên chi nhánh của mình."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return _need_login_response()
        if not _can_work_counter(u):
            if request.path.startswith("/api/"):
                return jsonify(error="Bạn không được giao trực quầy (thiếu quyền goiso.counter)."), 403
            return "Bạn không được giao trực quầy gọi số.", 403
        if not _is_goiso_admin(u) and u["branch_id"] != g.branch["id"]:
            if request.path.startswith("/api/"):
                return jsonify(error="Bạn không thuộc chi nhánh này."), 403
            return "Bạn không có quyền truy cập chi nhánh này.", 403
        g.user = u
        return view(*args, **kwargs)
    return wrapper


@bp.app_errorhandler(_SAOperationalError)
def _db_locked(e):
    msg = str(e)
    if "locked" in msg or "busy" in msg:
        text = ("CSDL đang bị một chương trình khác khoá (thường là DB Browser "
                "for SQLite / SQLiteStudio đang mở file hethong_v2.db). "
                "Hãy đóng chương trình đó rồi thử lại.")
        code = 503
    else:
        text = "Lỗi CSDL: " + msg
        code = 500
    if request.path.startswith("/api/"):
        return jsonify(error=text), code
    return text, code


# ----------------------------------------------------------------- SSE stream
@bp.route("/api/b/<code>/stream")
@resolve_branch
def stream():
    branch_id = g.branch["id"]

    def gen():
        q = queuelib.Queue(maxsize=64)
        with _sub_lock:
            _subscribers.setdefault(branch_id, set()).add(q)
        try:
            yield "retry: 3000\n\n"
            yield f"data: {json.dumps(ql.snapshot(branch_id), ensure_ascii=False)}\n\n"
            last_beat = time.time()
            while True:
                try:
                    data = q.get(timeout=10)
                    yield f"data: {data}\n\n"
                except queuelib.Empty:
                    pass
                if time.time() - last_beat > 10:
                    yield ": ping\n\n"
                    last_beat = time.time()
        finally:
            with _sub_lock:
                subs = _subscribers.get(branch_id)
                if subs:
                    subs.discard(q)

    resp = Response(stream_with_context(gen()), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"
    # KHÔNG đặt header "Connection" ở đây: đó là hop-by-hop header, waitress (PEP 3333)
    # sẽ ném AssertionError. Keep-alive do máy chủ/Cloudflare tự quản lý.
    return resp


# ----------------------------------------------------------------- trang web
# Toàn bộ giao diện (portal, bàn gọi số, màn hình, bảng chờ, đặt lịch...) giờ
# do Portal React (SPA) phục vụ — backend chỉ còn API JSON (trạng thái +
# thao tác). Các trang cũ (counter/display/board/booking/... và admin.html,
# vốn là Jinja) đã được thay bằng frontend/src/pages/goiso/*.jsx và
# frontend/src/pages/admin/*.


@bp.get("/api/b/<code>/screens")
@resolve_branch
def api_branch_screens():
    """Danh sách 'màn hình theo khu' của chi nhánh — công khai, dùng để lọc
    hiển thị ở màn hình TV / bảng chờ theo ?screen=<id>."""
    return jsonify(screens=db.get_screens(g.branch["id"]))


@bp.get("/api/b/<code>/counters")
@resolve_branch
@counter_guard
def api_branch_counters():
    """Danh sách quầy đang bật của chi nhánh — cho màn "Vào ca" chọn quầy."""
    counters = db.get_json_config("counters", {}, g.branch["id"]) or {}
    active = [
        {"id": k, **v}
        for k, v in sorted(counters.items(), key=lambda kv: kv[1].get("display_order", 99))
        if v.get("active", True)
    ]
    return jsonify(counters=active)


@bp.get("/api/booking/turnstile-key")
def api_booking_turnstile_key():
    """Site key Turnstile (public theo thiết kế) cho form đặt lịch React."""
    return jsonify(site_key=TURNSTILE_SITE_KEY)


# ----------------------------------------------------------------- API cấp số (kiosk)
@bp.post("/api/b/<code>/ticket")
@resolve_branch
@require_branch_key
def api_ticket():
    body = request.get_json(silent=True) or request.form
    prefix = (body.get("prefix") or "").strip().upper()
    if not prefix:
        return jsonify(error="Thiếu mã dịch vụ."), 400
    try:
        ticket = ql.issue_ticket(
            g.branch["id"], prefix,
            fullname=body.get("fullname", ""),
            cccd=body.get("cccd", ""),
            phone=body.get("phone", ""),
        )
    except ql.QueueError as e:
        return jsonify(error=str(e)), 409
    push_snapshot(g.branch["id"])
    return jsonify(ticket)


@bp.get("/api/b/<code>/state")
@resolve_branch
def api_state():
    return jsonify(ql.snapshot(g.branch["id"]))


@bp.get("/api/b/<code>/tts")
@resolve_branch
def api_tts():
    """Đọc số bằng giọng tiếng Việt phía máy chủ -> trả file mp3."""
    text = request.args.get("text", "")
    voice = request.args.get("voice", "") or db.get_extra(g.branch["id"]).get("tts_voice", "")
    if not tts_engine.available():
        return jsonify(error="Máy chủ chưa cài edge-tts."), 503
    try:
        path = tts_engine.get_or_make(text, voice)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception:  # noqa: BLE001
        return jsonify(error="Không tạo được âm thanh."), 502
    from flask import send_file
    resp = send_file(path, mimetype="audio/mpeg", conditional=True)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@bp.post("/api/b/<code>/checkin")
@resolve_branch
@require_branch_key
def api_checkin():
    body = request.get_json(silent=True) or {}
    try:
        ticket = bk.checkin(g.branch["id"], body.get("code", ""))
    except bk.BookingError as e:
        return jsonify(error=str(e)), 409
    except ql.QueueError as e:
        return jsonify(error=str(e)), 409
    push_snapshot(g.branch["id"])
    return jsonify(ticket)


@bp.get("/api/b/<code>/config/public")
@resolve_branch
def api_config_public():
    """Cấu hình công khai cho kiosk / màn hình (không có mật khẩu)."""
    branch_id = g.branch["id"]
    services = db.get_json_config("services", {}, branch_id) or {}
    day = db.today_str()
    with db.get_conn() as conn:
        issued = {
            r["prefix"]: r["c"]
            for r in conn.execute(
                "SELECT prefix, COUNT(*) c FROM goiso_queue WHERE branch_id=? AND date_record=? GROUP BY prefix",
                (branch_id, day),
            )
        }
    svc_out = {}
    for k, v in services.items():
        if not v.get("active", True):
            continue
        limit = int(v.get("daily_limit") or 0)
        used = issued.get(k, 0)
        svc_out[k] = {
            "name": v.get("name", k),
            "short": db.short_label(v, k),
            "color": v.get("color", "#0b5fa5"),
            "daily_limit": limit,
            "issued_today": used,
            "sold_out": bool(limit and used >= limit),
        }
    extra = db.get_extra(branch_id)
    return jsonify({
        "branch": {"code": g.branch["code"], "name": g.branch["name"],
                   "full_name": g.branch["full_name"]},
        "services": svc_out,
        "extra": {
            "ten_co_quan": extra.get("ten_co_quan", ""),
            "ten_chi_nhanh": g.branch["full_name"],
            "link_qr": extra.get("link_qr", ""),
            "qr_enabled": extra.get("qr_enabled", False),
            "lock_time_enabled": extra.get("lock_time_enabled", False),
            "lock_message": extra.get("lock_message", ""),
            "time_slots": extra.get("time_slots", []),
            "voice_rate": extra.get("voice_rate", 0.95),
            "voice_repeat": extra.get("voice_repeat", 2),
            "voice_template": extra.get("voice_template", "Xin mời số thứ tự {so}, đến quầy số {quay}"),
            "spotlight_seconds": extra.get("spotlight_seconds", 20),
            "tts_mode": extra.get("tts_mode", "server"),
            "tts_voice": extra.get("tts_voice", "vi-VN-HoaiMyNeural"),
            "footer_credit": extra.get("footer_credit", ""),
        },
        "time_open": ql.within_time_lock(branch_id),
    })


# ----------------------------------------------------------------- API quầy
def _staff():
    return (getattr(g, "user", None) or {}).get("full_name", "")


@bp.get("/api/b/<code>/counter/<path:counter_id>/view")
@resolve_branch
@counter_guard
def api_counter_view(counter_id):
    return jsonify(ql.counter_view(g.branch["id"], counter_id))


@bp.post("/api/b/<code>/counter/<path:counter_id>/login")
@resolve_branch
@counter_guard
def api_counter_login(counter_id):
    ql.set_counter_status(g.branch["id"], counter_id, "active", staff_name=_staff())
    push_snapshot(g.branch["id"])
    return jsonify(ql.counter_view(g.branch["id"], counter_id))


@bp.post("/api/b/<code>/counter/<path:counter_id>/next")
@resolve_branch
@counter_guard
def api_counter_next(counter_id):
    try:
        called = ql.call_next(g.branch["id"], counter_id, staff_name=_staff())
    except ql.QueueError as e:
        return jsonify(error=str(e)), 409
    broadcast(g.branch["id"], {"type": "call", **called})
    push_snapshot(g.branch["id"])
    return jsonify(called)


@bp.post("/api/b/<code>/counter/<path:counter_id>/recall")
@resolve_branch
@counter_guard
def api_counter_recall(counter_id):
    try:
        called = ql.recall(g.branch["id"], counter_id)
    except ql.QueueError as e:
        return jsonify(error=str(e)), 409
    broadcast(g.branch["id"], {"type": "call", **called})
    return jsonify(called)


@bp.post("/api/b/<code>/counter/<path:counter_id>/done")
@resolve_branch
@counter_guard
def api_counter_done(counter_id):
    try:
        ql.finish_current(g.branch["id"], counter_id)
    except ql.QueueError as e:
        return jsonify(error=str(e)), 409
    push_snapshot(g.branch["id"])
    return jsonify(ql.counter_view(g.branch["id"], counter_id))


@bp.post("/api/b/<code>/counter/<path:counter_id>/missed")
@resolve_branch
@counter_guard
def api_counter_missed(counter_id):
    try:
        ql.mark_missed(g.branch["id"], counter_id)
    except ql.QueueError as e:
        return jsonify(error=str(e)), 409
    push_snapshot(g.branch["id"])
    return jsonify(ql.counter_view(g.branch["id"], counter_id))


@bp.post("/api/b/<code>/counter/<path:counter_id>/call")
@resolve_branch
@counter_guard
def api_counter_call_specific(counter_id):
    body = request.get_json(silent=True) or {}
    try:
        called = ql.call_specific(
            g.branch["id"], counter_id, body.get("full_no", ""), staff_name=_staff(),
        )
    except ql.QueueError as e:
        return jsonify(error=str(e)), 409
    broadcast(g.branch["id"], {"type": "call", **called})
    push_snapshot(g.branch["id"])
    return jsonify(called)


@bp.post("/api/b/<code>/counter/<path:counter_id>/status")
@resolve_branch
@counter_guard
def api_counter_status(counter_id):
    body = request.get_json(silent=True) or {}
    try:
        r = ql.set_counter_status(g.branch["id"], counter_id, (body.get("status") or "").strip())
    except ql.QueueError as e:
        return jsonify(error=str(e)), 409
    push_snapshot(g.branch["id"])
    return jsonify(r)


# ----------------------------------------------------------------- API admin
# Quản lý tài khoản đã HỢP NHẤT về platform (Phase 5). Endpoint cũ chỉ còn trỏ sang.
@bp.get("/api/admin/users")
@admin_required
def api_admin_users():
    return jsonify(
        users=[],
        branches=db.list_branches(),
        moved="/api/users",
        message="Quản lý tài khoản đã chuyển sang trang Quản trị hệ thống (/api/users).",
    )


@bp.post("/api/admin/users")
@admin_required
def api_admin_users_write():
    return jsonify(
        error="Quản lý tài khoản đã chuyển sang platform. Dùng API /api/users.",
        moved="/api/users",
    ), 410


@bp.get("/api/admin/branches")
@admin_required
def api_admin_branches():
    return jsonify(branches=db.list_branches())


@bp.post("/api/admin/branches")
@admin_required
def api_admin_branches_write():
    body = request.get_json(silent=True) or {}
    action = body.get("action", "")
    code = (body.get("code") or "").strip().lower()
    try:
        if action == "create":
            b = db.create_branch(code, body.get("name", ""), body.get("full_name", ""),
                                 body.get("address", ""))
            return jsonify(ok=True, branch=b)
        if action == "update":
            b = db.update_branch(code, **{k: body[k] for k in
                                         ("name", "full_name", "address", "active", "display_order")
                                         if k in body})
            return jsonify(ok=True, branch=b)
        if action == "delete":
            db.delete_branch(code)
            return jsonify(ok=True)
        if action in ("regen_key", "regen_display_token"):
            field = "api_key" if action == "regen_key" else "display_token"
            token = db.regen_branch_field(code, field)
            return jsonify(ok=True, field=field, value=token)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(error="action không hợp lệ."), 400


@bp.get("/api/admin/b/<code>/config")
@admin_required
@resolve_branch
def api_admin_get_config():
    bid = g.branch["id"]
    return jsonify({
        "branch": g.branch,
        "services": db.get_json_config("services", {}, bid),
        "counters": db.get_json_config("counters", {}, bid),
        "screens": db.get_screens(bid),
        "extra": db.get_extra(bid),
        "booking": db.get_booking_config(bid),
    })


@bp.post("/api/admin/b/<code>/config")
@admin_required
@resolve_branch
def api_admin_set_config():
    bid = g.branch["id"]
    body = request.get_json(silent=True) or {}
    if "services" in body:
        db.set_json_config("services", body["services"], bid)
    if "counters" in body:
        db.set_json_config("counters", body["counters"], bid)
    if "screens" in body:
        # chuẩn hoá id (slug, không rỗng, không trùng) + bỏ màn hình không tên
        clean = [sc for sc in db.get_screens_from_list(body["screens"]) if sc["name"]]
        db.set_json_config("screens", clean, bid)
    if "extra" in body:
        merged = db.get_json_config("extra", {}, bid) or {}
        merged.update(body["extra"])
        db.set_json_config("extra", merged, bid)
    if "booking" in body:
        merged = db.get_json_config("booking", {}, bid) or {}
        merged.update(body["booking"])
        db.set_json_config("booking", merged, bid)
    push_snapshot(bid)
    return jsonify(ok=True)


@bp.get("/api/admin/stats")
@admin_required
def api_admin_stats():
    which = request.args.get("branch", "all")
    day = db.today_str()
    branches = db.list_branches() if which == "all" else [db.get_branch(which)]
    branches = [b for b in branches if b]
    if not branches:
        return jsonify(error="Không có chi nhánh."), 404

    with db.get_conn() as conn:
        out = []
        for b in branches:
            bid = b["id"]
            by_service = [
                {"prefix": r["prefix"], "issued": r["issued"], "done": r["done"] or 0,
                 "missed": r["missed"] or 0, "waiting": r["waiting"] or 0}
                for r in conn.execute(
                    """SELECT prefix, COUNT(*) issued,
                              SUM(status='done') done, SUM(status='missed') missed,
                              SUM(status='waiting') waiting
                       FROM goiso_queue WHERE branch_id=? AND date_record=?
                       GROUP BY prefix ORDER BY prefix""",
                    (bid, day),
                )
            ]
            avg_wait = conn.execute(
                """SELECT AVG(TIMESTAMPDIFF(SECOND, time_issue, time_start))
                   FROM goiso_queue WHERE branch_id=? AND date_record=?
                     AND time_start IS NOT NULL AND time_issue IS NOT NULL""",
                (bid, day),
            ).fetchone()[0]
            total = conn.execute(
                "SELECT COALESCE(count,0) FROM goiso_visitor_stats WHERE branch_id=? AND date_record=?",
                (bid, day),
            ).fetchone()
            out.append({
                "code": b["code"], "name": b["name"],
                "today_total": total[0] if total else 0,
                "avg_wait_seconds": round(avg_wait) if avg_wait else 0,
                "by_service": by_service,
            })
        visitors = []
        if which != "all":
            visitors = [
                {"date": r["date_record"], "count": r["count"]}
                for r in conn.execute(
                    "SELECT * FROM goiso_visitor_stats WHERE branch_id=? ORDER BY date_record DESC LIMIT 30",
                    (branches[0]["id"],),
                )
            ]
    return jsonify({"today": day, "scope": which, "branches": out, "visitors": visitors})


@bp.get("/api/admin/b/<code>/appointments")
@admin_required
@resolve_branch
def api_admin_appointments():
    d = request.args.get("date", db.today_str())
    with db.get_conn() as conn:
        rows = [
            {"code": r["code"], "token": r["token"], "prefix": r["prefix"],
             "slot_start": r["slot_start"], "slot_end": r["slot_end"],
             "status": r["status"], "citizen_name": r["citizen_name"],
             "cccd": r["cccd"], "phone": r["phone"],
             "created_at": r["created_at"], "checkin_at": r["checkin_at"]}
            for r in conn.execute(
                "SELECT * FROM goiso_appointments WHERE branch_id=? AND slot_date=? "
                "ORDER BY slot_start, created_at",
                (g.branch["id"], d),
            )
        ]
    return jsonify({"date": d, "appointments": rows})


@bp.post("/api/admin/b/<code>/appointments/cancel")
@admin_required
@resolve_branch
def api_admin_appt_cancel():
    body = request.get_json(silent=True) or {}
    try:
        bk.cancel(body.get("token", ""))
    except bk.BookingError as e:
        return jsonify(error=str(e)), 409
    return jsonify(ok=True)


@bp.post("/api/admin/b/<code>/reset-today")
@admin_required
@resolve_branch
def api_admin_reset_today():
    bid = g.branch["id"]
    day = db.today_str()
    with db.LOCK, db.get_conn() as conn:
        conn.execute("DELETE FROM goiso_queue WHERE branch_id=? AND date_record=?", (bid, day))
        conn.execute("DELETE FROM goiso_visitor_stats WHERE branch_id=? AND date_record=?", (bid, day))
        conn.execute("UPDATE goiso_counters_status SET last_num='', status='offline' WHERE branch_id=?", (bid,))
        conn.execute(
            "UPDATE goiso_appointments SET status='cancelled' "
            "WHERE branch_id=? AND slot_date=? AND status='booked'",
            (bid, day),
        )
    push_snapshot(bid)
    return jsonify(ok=True)


# ----------------------------------------------------------------- API kiosk / thiết bị
@bp.get("/api/ping")
def api_ping():
    """Xác nhận đây là GoSo Server (dùng cho Configurator 'Kiểm tra kết nối')."""
    return jsonify(ok=True, service="goso-kiosk-server",
                   server_version=SERVER_VERSION, time=db.now_str())


@bp.get("/api/branches")
def api_branches():
    """Danh sách chi nhánh đang hoạt động (công khai, cho Configurator chọn chi nhánh)."""
    return jsonify(branches=[
        {"id": b["id"], "code": b["code"], "name": b["name"], "full_name": b["full_name"]}
        for b in db.list_branches(active_only=True)
    ])


@bp.get("/api/kiosk/version")
def api_kiosk_version():
    """Bản kiosk mới nhất áp dụng cho (chi nhánh / thiết bị). v1: 1 bản chung, có
    đường mở rộng rollout theo branch_code về sau."""
    rel = db.get_kiosk_release(request.args.get("branch_code") or None)
    return jsonify(rel)


@bp.post("/api/b/<code>/heartbeat")
@resolve_branch
@require_branch_key
def api_kiosk_heartbeat():
    body = request.get_json(silent=True) or {}
    did = (body.get("device_id") or "").strip()
    if not did:
        return jsonify(error="Thiếu device_id."), 400
    try:
        dev = db.upsert_device(
            did, branch_code=g.branch["code"],
            name=body.get("name", ""), version=body.get("version", ""),
            printer=body.get("printer", ""), paper_mm=int(body.get("paper_mm") or 80),
            status=body.get("status", "online"),
            update_status=body.get("update_status", ""),
        )
    except (ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400
    return jsonify(ok=True, device=dev,
                   release=db.get_kiosk_release(g.branch["code"]))


@bp.get("/api/admin/devices")
@admin_required
def api_admin_devices():
    return jsonify(devices=db.list_devices(), release=db.get_kiosk_release())


@bp.post("/api/admin/kiosk-release")
@admin_required
def api_admin_set_kiosk_release():
    b = request.get_json(silent=True) or {}
    rel = db.set_kiosk_release(
        version=b.get("version"), download_url=b.get("download_url"),
        sha256=b.get("sha256"), mandatory=b.get("mandatory"),
        release_notes=b.get("release_notes"),
        min_supported_version=b.get("min_supported_version"),
    )
    return jsonify(ok=True, release=rel)


# ----------------------------------------------------------------- API đặt lịch online (công khai)
@bp.get("/api/booking/branches")
def api_booking_branches():
    return jsonify(branches=bk.public_branches())


@bp.get("/api/booking/<code>/slots")
@resolve_branch
def api_booking_slots():
    try:
        slots = bk.list_slots(g.branch["id"], request.args.get("date", ""),
                              (request.args.get("prefix", "") or "").upper())
    except bk.BookingError as e:
        return jsonify(error=str(e)), 400
    return jsonify({"slots": slots})


@bp.post("/api/booking/<code>/book")
@resolve_branch
def api_booking_book():
    body = request.get_json(silent=True) or {}
    ip = _client_ip()
    if not bk.rate_limit_ok(ip):
        return jsonify(error="Bạn đã đặt quá nhiều lần trong 1 giờ. Vui lòng thử lại sau."), 429
    if not bk.verify_turnstile(g.branch["id"], body.get("turnstile_token", ""), ip):
        return jsonify(error="Xác thực chống spam thất bại. Vui lòng tải lại trang."), 400
    try:
        appt = bk.create_appointment(
            g.branch["id"], (body.get("prefix", "") or "").upper(),
            body.get("slot_date", ""), body.get("slot_start", ""),
            body.get("citizen_name", ""), body.get("cccd", ""), body.get("phone", ""),
            ip=ip,
        )
    except bk.BookingError as e:
        return jsonify(error=str(e)), 409
    return jsonify(appt)


@bp.get("/api/booking/appt/<token>")
def api_booking_appt(token):
    try:
        return jsonify(bk.appointment_view(token))
    except bk.BookingError as e:
        return jsonify(error=str(e)), 404


@bp.post("/api/booking/appt/<token>/cancel")
def api_booking_appt_cancel(token):
    try:
        return jsonify(bk.cancel(token))
    except bk.BookingError as e:
        return jsonify(error=str(e)), 409


# ----------------------------------------------------------------- sweeper nền
def _sweeper():
    while True:
        time.sleep(300)
        try:
            bk.expire_stale()
        except Exception:  # noqa: BLE001
            pass


threading.Thread(target=_sweeper, daemon=True).start()
