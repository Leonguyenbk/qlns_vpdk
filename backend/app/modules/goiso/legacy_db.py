"""Truy cập CSDL cho hệ gọi số — Phase 6: chạy trên MySQL dùng chung với nhân sự.

Giữ NGUYÊN chữ ký hàm và nghiệp vụ như bản SQLite; chỉ thay tầng kết nối bằng
một shim SQLAlchemy (`get_conn()`), và mọi bảng mang tiền tố `goiso_`.
`goiso_config.branch_id = 0` là cấu hình toàn cục.

Bảng do Alembic quản lý (0006_goiso_tables); `init_db()` chỉ còn là no-op.
"""
import json
import os
import re
import secrets
import threading
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import text as _sql_text

# SQLite ghi tuần tự; giữ khoá này để tuần tự hoá các thao tác đọc-sửa-ghi phức hợp.
LOCK = threading.RLock()

GLOBAL = 0  # branch_id cho cấu hình toàn cục

# ------------------------------------------------------------------ shim kết nối
_engine = None
_engine_lock = threading.Lock()
_local = threading.local()


def _get_engine():
    global _engine
    if _engine is not None:
        return _engine
    with _engine_lock:
        if _engine is not None:
            return _engine
        override = os.environ.get("GOISO_DATABASE_URL")
        if not override:
            # Dùng chung engine với Flask-SQLAlchemy khi đang trong app context
            # (nhờ đó test in-memory và pool production đều nhất quán).
            try:
                from flask import current_app

                if current_app:
                    from ...extensions import db as _fsa

                    _engine = _fsa.engine
                    return _engine
            except Exception:  # noqa: BLE001
                pass
        url = override or os.environ["DATABASE_URL"]
        _engine = create_engine(
            url, pool_pre_ping=True, pool_recycle=280, future=True
        )
    return _engine


class _Row:
    """Hàng kết quả hỗ trợ cả r["cột"] lẫn r[0], dict(r), 'x' in r."""

    __slots__ = ("_m", "_k")

    def __init__(self, mapping):
        self._m = dict(mapping)
        self._k = list(mapping.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._m[self._k[key]]
        return self._m[key]

    def get(self, key, default=None):
        return self._m.get(key, default)

    def keys(self):
        return list(self._k)

    def __iter__(self):
        return iter(self._m.values())

    def __contains__(self, key):
        return key in self._m


class _Result:
    def __init__(self, res):
        self._res = res
        self.lastrowid = getattr(res, "lastrowid", None)
        try:
            self.rowcount = res.rowcount
        except Exception:  # noqa: BLE001
            self.rowcount = -1

    def fetchone(self):
        row = self._res.fetchone()
        return _Row(row._mapping) if row is not None else None

    def fetchall(self):
        return [_Row(r._mapping) for r in self._res.fetchall()]

    def __iter__(self):
        for r in self._res:
            yield _Row(r._mapping)


def _convert(sql, params):
    """?-placeholder -> :_p0.. cho SQLAlchemy text()."""
    if not params:
        return sql, {}
    seq = list(params)
    out, i, binds = [], 0, {}
    for ch in sql:
        if ch == "?":
            out.append(f":_p{i}")
            binds[f"_p{i}"] = seq[i]
            i += 1
        else:
            out.append(ch)
    return "".join(out), binds


_ON_CONFLICT_RE = re.compile(
    r"ON\s+CONFLICT\s*\([^)]*\)\s+DO\s+UPDATE\s+SET\s+", re.IGNORECASE
)


def _to_mysql_dialect(sql):
    """SQL viết theo SQLite -> MySQL: upsert ON CONFLICT(...) -> ON DUPLICATE KEY."""
    m = _ON_CONFLICT_RE.search(sql)
    if not m:
        return sql
    head, tail = sql[: m.start()], sql[m.end():]
    tail = re.sub(r"excluded\.(\w+)", r"VALUES(\1)", tail)
    return head + "ON DUPLICATE KEY UPDATE " + tail


class _Conn:
    """Bắt chước sqlite3.Connection dùng-một-lần trong khối `with`.

    Lồng nhau trong cùng một luồng -> dùng chung 1 connection + 1 transaction,
    commit khi khối ngoài cùng thoát (khớp hành vi 'với LOCK' của bản cũ).
    """

    def __init__(self):
        if getattr(_local, "conn", None) is None:
            _local.conn = _get_engine().connect()
            _local.tx = _local.conn.begin()
            _local.depth = 0
        _local.depth += 1
        self._c = _local.conn
        self._mysql = self._c.dialect.name == "mysql"

    def execute(self, sql, params=()):
        if self._mysql and "ON CONFLICT" in sql:
            sql = _to_mysql_dialect(sql)
        q, binds = _convert(sql, params)
        return _Result(self._c.execute(_sql_text(q), binds))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        _local.depth -= 1
        if _local.depth > 0:
            return False
        try:
            if exc_type is not None:
                _local.tx.rollback()
            else:
                _local.tx.commit()
        finally:
            _local.conn.close()
            _local.conn = None
            _local.tx = None
        return False


def get_conn():
    return _Conn()


def init_db():
    """No-op: schema goiso_* do Alembic (0006_goiso_tables) quản lý."""
    return None


# --------------------------------------------------------------- mẫu cấu hình
DEFAULT_COUNTERS = {
    "Quầy số 01": {"active": True, "staff": "", "prefix": "A", "display_order": 1},
    "Quầy số 02": {"active": True, "staff": "", "prefix": "A", "display_order": 2},
    "Quầy số 03": {"active": True, "staff": "", "prefix": "B", "display_order": 3},
    "Quầy số 04": {"active": True, "staff": "", "prefix": "C", "display_order": 4},
    "Quầy số 05": {"active": True, "staff": "", "prefix": "A,B,C", "display_order": 5},
}

DEFAULT_SCREENS = []

DEFAULT_SERVICES = {
    "A": {"name": "ĐĂNG KÝ ĐẤT ĐAI", "short": "Đăng ký đất đai",
          "color": "#3498db", "daily_limit": 200, "active": True},
    "B": {"name": "GIAO DỊCH BẢO ĐẢM", "short": "Giao dịch bảo đảm",
          "color": "#e67e22", "daily_limit": 200, "active": True},
    "C": {"name": "TRẢ KẾT QUẢ", "short": "Trả kết quả",
          "color": "#27ae60", "daily_limit": 300, "active": True},
}

DEFAULT_EXTRA = {
    "ten_co_quan": "VĂN PHÒNG ĐĂNG KÝ ĐẤT ĐAI",
    "link_qr": "",
    "logo_path": "",
    "qr_enabled": False,
    "background_color": "#f5f7fa",
    "counter_pin": "",
    "lock_time_enabled": True,
    "time_slots": [
        {"start_hour": 6, "start_minute": 15, "end_hour": 11, "end_minute": 15},
        {"start_hour": 13, "start_minute": 15, "end_hour": 15, "end_minute": 30},
    ],
    "lock_message": "Hiện tại chưa đến giờ lấy số hoặc đã hết giờ!\nVui lòng quay lại trong khung giờ Sáng 6:15-11:15, Chiều 13:15-15:30.",
    "allow_saturday": False,
    "allow_sunday": False,
    "voice_rate": 0.95,
    "voice_repeat": 2,
    "voice_template": "Xin mời số thứ tự {so}, đến quầy số {quay}",
    "tts_mode": "server",
    "tts_voice": "vi-VN-HoaiMyNeural",
    "spotlight_seconds": 20,
    "recent_count": 8,
    "footer_credit": "Phòng Dữ liệu - Thông tin đất đai\nTổ Ứng dụng và Phát triển công nghệ",
}

DEFAULT_BOOKING = {
    "enabled": False,
    "open_days_ahead": 3,
    "slot_minutes": 30,
    "windows": [
        {"start": "07:30", "end": "11:00"},
        {"start": "13:30", "end": "16:00"},
    ],
    "capacity_per_slot": {"_default": 4},
    "max_active_per_cccd": 1,
    "checkin_grace_minutes": 15,
    "online_priority": False,
    "turnstile": True,
}


# ---------------------------------------------------------------- config helpers
def get_config(key, default=None, branch_id=GLOBAL):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM goiso_config WHERE branch_id=? AND `key`=?", (branch_id, key)
        ).fetchone()
    return default if row is None else row[0]


def get_json_config(key, default=None, branch_id=GLOBAL):
    raw = get_config(key, None, branch_id)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default


def set_json_config(key, obj, branch_id=GLOBAL):
    set_config(key, json.dumps(obj, ensure_ascii=False), branch_id)


def set_config(key, value, branch_id=GLOBAL):
    with LOCK, get_conn() as conn:
        conn.execute(
            "INSERT INTO goiso_config(branch_id, `key`, value) VALUES(?, ?, ?) "
            "ON CONFLICT(branch_id, `key`) DO UPDATE SET value=excluded.value",
            (branch_id, key, value),
        )


def get_extra(branch_id):
    data = dict(DEFAULT_EXTRA)
    data.update(get_json_config("extra", {}, branch_id) or {})
    return data


def get_booking_config(branch_id):
    data = dict(DEFAULT_BOOKING)
    data.update(get_json_config("booking", {}, branch_id) or {})
    return data


def slugify(s):
    s = strip_accents(s or "").lower()
    out = []
    for ch in s:
        out.append(ch if ch.isalnum() else "-")
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug


def get_screens_from_list(raw):
    out, seen = [], set()
    for i, sc in enumerate(raw or []):
        if not isinstance(sc, dict):
            continue
        name = str(sc.get("name", "")).strip()
        sid = slugify(sc.get("id") or name) or f"man-hinh-{i + 1}"
        base, n = sid, 2
        while sid in seen:
            sid = f"{base}-{n}"
            n += 1
        seen.add(sid)
        counters = [str(c) for c in (sc.get("counters") or []) if str(c).strip()]
        out.append({"id": sid, "name": name, "counters": counters})
    return out


def get_screens(branch_id):
    return get_screens_from_list(get_json_config("screens", [], branch_id) or [])


def resolve_screen(branch_id, screen_id):
    sid = (screen_id or "").strip()
    if not sid:
        return None
    for sc in get_screens(branch_id):
        if sc["id"] == sid:
            return sc
    return None


# ---------------------------------------------------------------- branch helpers
_branch_cache = {}
_branch_cache_by_id = {}
_branch_cache_lock = threading.Lock()


def _invalidate_branch_cache():
    with _branch_cache_lock:
        _branch_cache.clear()
        _branch_cache_by_id.clear()


def _row_to_branch(row):
    return {
        "id": row["id"], "code": row["code"], "name": row["name"],
        "full_name": row["full_name"], "address": row["address"] or "",
        "active": bool(row["active"]), "display_order": row["display_order"],
        "api_key": row["api_key"], "display_token": row["display_token"],
        "created_at": row["created_at"],
    }


def get_branch(code):
    code = (code or "").strip().lower()
    if not code:
        return None
    with _branch_cache_lock:
        if code in _branch_cache:
            return _branch_cache[code]
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM goiso_branches WHERE code=?", (code,)).fetchone()
    b = _row_to_branch(row) if row else None
    with _branch_cache_lock:
        _branch_cache[code] = b
        if b:
            _branch_cache_by_id[b["id"]] = b
    return b


def get_branch_by_id(branch_id):
    with _branch_cache_lock:
        if branch_id in _branch_cache_by_id:
            return _branch_cache_by_id[branch_id]
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM goiso_branches WHERE id=?", (branch_id,)).fetchone()
    b = _row_to_branch(row) if row else None
    if b:
        with _branch_cache_lock:
            _branch_cache_by_id[branch_id] = b
            _branch_cache[b["code"]] = b
    return b


def list_branches(active_only=False):
    q = "SELECT * FROM goiso_branches"
    if active_only:
        q += " WHERE active=1"
    q += " ORDER BY display_order, code"
    with get_conn() as conn:
        return [_row_to_branch(r) for r in conn.execute(q)]


def gen_token(nbytes=24):
    return secrets.token_urlsafe(nbytes)


def create_branch(code, name, full_name, address="", display_order=None):
    code = (code or "").strip().lower()
    if not code or not code.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Mã chi nhánh chỉ gồm chữ/số/gạch, ví dụ 'bmt'.")
    with LOCK, get_conn() as conn:
        if conn.execute("SELECT 1 FROM goiso_branches WHERE code=?", (code,)).fetchone():
            raise ValueError(f"Chi nhánh '{code}' đã tồn tại.")
        if display_order is None:
            mx = conn.execute(
                "SELECT COALESCE(MAX(display_order), 0) FROM goiso_branches"
            ).fetchone()[0]
            display_order = mx + 1
        cur = conn.execute(
            """INSERT INTO goiso_branches
                 (code, name, full_name, address, active, display_order,
                  api_key, display_token, created_at)
               VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)""",
            (code, name.strip(), full_name.strip(), address.strip(), display_order,
             gen_token(24), gen_token(16), now_str()),
        )
        bid = cur.lastrowid
        for key, obj in (("services", DEFAULT_SERVICES), ("counters", DEFAULT_COUNTERS),
                         ("screens", DEFAULT_SCREENS), ("extra", {}), ("booking", {})):
            conn.execute(
                "INSERT INTO goiso_config(branch_id, `key`, value) VALUES(?, ?, ?)",
                (bid, key, json.dumps(obj, ensure_ascii=False)),
            )
    _invalidate_branch_cache()
    return get_branch(code)


def update_branch(code, **fields):
    allowed = {"name", "full_name", "address", "active", "display_order"}
    sets, vals = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            vals.append(int(v) if k in ("active", "display_order") else str(v).strip())
    if not sets:
        return get_branch(code)
    vals.append((code or "").strip().lower())
    with LOCK, get_conn() as conn:
        conn.execute(f"UPDATE goiso_branches SET {', '.join(sets)} WHERE code=?", vals)
    _invalidate_branch_cache()
    return get_branch(code)


def regen_branch_field(code, field):
    if field not in ("api_key", "display_token"):
        raise ValueError("field phải là api_key hoặc display_token.")
    token = gen_token(24 if field == "api_key" else 16)
    with LOCK, get_conn() as conn:
        conn.execute(f"UPDATE goiso_branches SET {field}=? WHERE code=?",
                     (token, (code or "").strip().lower()))
    _invalidate_branch_cache()
    return token


def delete_branch(code):
    code = (code or "").strip().lower()
    with LOCK, get_conn() as conn:
        row = conn.execute("SELECT id FROM goiso_branches WHERE code=?", (code,)).fetchone()
        if not row:
            return
        bid = row["id"]
        for t in ("goiso_queue", "goiso_counters_status", "goiso_visitor_stats",
                  "goiso_appointments"):
            conn.execute(f"DELETE FROM {t} WHERE branch_id=?", (bid,))
        conn.execute("DELETE FROM goiso_config WHERE branch_id=?", (bid,))
        conn.execute("DELETE FROM goiso_branches WHERE id=?", (bid,))
    _invalidate_branch_cache()


# ---------------------------------------------------------------- tiện ích tên
def strip_accents(s):
    import unicodedata
    s = (s or "").replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


# ---------------------------------------------------------------- thiết bị kiosk
def upsert_device(device_id, **fields):
    device_id = (device_id or "").strip()
    if not device_id:
        raise ValueError("Thiếu device_id.")
    cols = ("branch_code", "name", "version", "printer", "paper_mm",
            "status", "update_status", "extra")
    vals = {k: fields[k] for k in cols if k in fields and fields[k] is not None}
    if "extra" in vals and not isinstance(vals["extra"], str):
        vals["extra"] = json.dumps(vals["extra"], ensure_ascii=False)
    now = now_str()
    with LOCK, get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM goiso_devices WHERE device_id=?", (device_id,)
        ).fetchone()
        if exists:
            if vals:
                sets = ", ".join(f"{k}=?" for k in vals)
                conn.execute(f"UPDATE goiso_devices SET {sets}, last_seen=? WHERE device_id=?",
                             (*vals.values(), now, device_id))
            else:
                conn.execute("UPDATE goiso_devices SET last_seen=? WHERE device_id=?",
                             (now, device_id))
        else:
            keys = ["device_id", "first_seen", "last_seen", *vals.keys()]
            conn.execute(
                f"INSERT INTO goiso_devices ({', '.join(keys)}) "
                f"VALUES ({', '.join('?' * len(keys))})",
                (device_id, now, now, *vals.values()),
            )
    return get_device(device_id)


def get_device(device_id):
    with get_conn() as conn:
        r = conn.execute(
            "SELECT * FROM goiso_devices WHERE device_id=?", (device_id,)
        ).fetchone()
    return dict(r) if r else None


def list_devices():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM goiso_devices ORDER BY branch_code, device_id")]


# --------- phát hành bản kiosk (auto-update). Lưu ở goiso_config key 'kiosk_release'
_KIOSK_RELEASE_DEFAULT = {
    "version": "", "download_url": "", "sha256": "",
    "mandatory": False, "release_notes": "", "min_supported_version": "",
}


def get_kiosk_release(branch_code=None):
    data = dict(_KIOSK_RELEASE_DEFAULT)
    data.update(get_json_config("kiosk_release", {}, GLOBAL) or {})
    if branch_code:
        b = get_branch(branch_code)
        if b:
            override = get_json_config("kiosk_release", None, b["id"])
            if override:
                data.update(override)
    return data


def set_kiosk_release(**fields):
    data = dict(_KIOSK_RELEASE_DEFAULT)
    data.update(get_json_config("kiosk_release", {}, GLOBAL) or {})
    for k in _KIOSK_RELEASE_DEFAULT:
        if k in fields and fields[k] is not None:
            data[k] = fields[k]
    set_json_config("kiosk_release", data, GLOBAL)
    return data


# ---------------------------------------------------------------- domain helpers
def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def session_now():
    return "Sáng" if datetime.now().hour < 12 else "Chiều"


def full_no(prefix, number):
    return f"{prefix}-{int(number):03d}"


def short_label(svc, code=""):
    if not svc:
        return code
    s = (svc.get("short") or "").strip()
    if s:
        return s
    name = (svc.get("name") or code or "").strip()
    head = name.split("(")[0].strip(" ,;-")
    if len(head) > 30:
        head = head[:29].rstrip() + "…"
    return head or code
