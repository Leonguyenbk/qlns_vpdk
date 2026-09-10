"""Test nghiệp vụ hàng đợi goiso (cấp số / gọi số / hoàn thành) trên shim SQLAlchemy.

Phase 6: legacy_db chạy qua SQLAlchemy. Test trỏ vào một file SQLite tạm riêng
(GOISO_DATABASE_URL) và tự dựng các bảng goiso_* tương đương migration 0006.
"""
from __future__ import annotations

import importlib

import pytest
from sqlalchemy import create_engine, text

_DDL = [
    """CREATE TABLE goiso_branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT, code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL, full_name VARCHAR(255) NOT NULL,
        address VARCHAR(255) DEFAULT '', active INTEGER DEFAULT 1,
        display_order INTEGER DEFAULT 99, api_key VARCHAR(64) NOT NULL,
        display_token VARCHAR(64) NOT NULL, created_at VARCHAR(30))""",
    """CREATE TABLE goiso_config (branch_id INTEGER NOT NULL DEFAULT 0,
        `key` VARCHAR(64) NOT NULL, value TEXT, PRIMARY KEY (branch_id, `key`))""",
    """CREATE TABLE goiso_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT, branch_id INTEGER NOT NULL,
        prefix VARCHAR(16), number INTEGER, status VARCHAR(16),
        counter VARCHAR(64) DEFAULT '', staff_name VARCHAR(255) DEFAULT '',
        date_record VARCHAR(10), time_issue VARCHAR(30), time_start VARCHAR(30),
        time_done VARCHAR(30), fullname VARCHAR(255) DEFAULT '', cccd VARCHAR(20) DEFAULT '',
        phone VARCHAR(20) DEFAULT '', session VARCHAR(10) DEFAULT '',
        source VARCHAR(16) DEFAULT 'kiosk', priority INTEGER DEFAULT 0, appointment_id INTEGER)""",
    """CREATE TABLE goiso_counters_status (branch_id INTEGER NOT NULL,
        counter_id VARCHAR(64) NOT NULL, staff_name VARCHAR(255) DEFAULT '',
        status VARCHAR(16) DEFAULT 'offline', last_num VARCHAR(16) DEFAULT '',
        last_update VARCHAR(30), PRIMARY KEY (branch_id, counter_id))""",
    """CREATE TABLE goiso_visitor_stats (branch_id INTEGER NOT NULL,
        date_record VARCHAR(10) NOT NULL, count INTEGER DEFAULT 0,
        PRIMARY KEY (branch_id, date_record))""",
    """CREATE TABLE goiso_appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, branch_id INTEGER NOT NULL,
        prefix VARCHAR(16) NOT NULL, slot_date VARCHAR(10) NOT NULL,
        slot_start VARCHAR(5) NOT NULL, slot_end VARCHAR(5) NOT NULL,
        code VARCHAR(16) NOT NULL, token VARCHAR(64) NOT NULL UNIQUE,
        citizen_name VARCHAR(255) DEFAULT '', cccd VARCHAR(20) DEFAULT '',
        phone VARCHAR(20) DEFAULT '', status VARCHAR(16) DEFAULT 'booked',
        created_at VARCHAR(30), checkin_at VARCHAR(30), queue_id INTEGER, ip VARCHAR(64) DEFAULT '')""",
    """CREATE TABLE goiso_devices (device_id VARCHAR(128) PRIMARY KEY,
        branch_code VARCHAR(50) DEFAULT '', name VARCHAR(255) DEFAULT '',
        version VARCHAR(30) DEFAULT '', printer VARCHAR(255) DEFAULT '',
        paper_mm INTEGER DEFAULT 80, status VARCHAR(16) DEFAULT 'online',
        update_status VARCHAR(64) DEFAULT '', first_seen VARCHAR(30),
        last_seen VARCHAR(30), extra TEXT)""",
]


@pytest.fixture
def goiso_db(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'goiso.db'}"
    monkeypatch.setenv("GOISO_DATABASE_URL", url)

    from app.modules.goiso import legacy_db

    monkeypatch.setattr(legacy_db, "_engine", None)  # buộc tạo engine mới theo override
    eng = create_engine(url)
    with eng.begin() as c:
        for stmt in _DDL:
            c.execute(text(stmt))
    legacy_db._invalidate_branch_cache()

    ql = importlib.import_module("app.modules.goiso.queue_logic")
    branch = legacy_db.create_branch("t1", "Test", "Chi nhánh Test")
    legacy_db.set_json_config("extra", {"lock_time_enabled": False}, branch["id"])
    yield branch, ql, legacy_db
    legacy_db._engine = None
    legacy_db._invalidate_branch_cache()


def test_issue_call_finish_flow(goiso_db):
    branch, ql, db = goiso_db
    bid = branch["id"]

    t1 = ql.issue_ticket(bid, "A")
    t2 = ql.issue_ticket(bid, "A")
    assert (t1["number"], t2["number"]) == (1, 2)
    assert t1["full_no"] == "A-001"

    called = ql.call_next(bid, "Quầy số 01", staff_name="NV Test")
    assert called["full_no"] == "A-001"
    assert called["counter_id"] == "Quầy số 01"

    view = ql.counter_view(bid, "Quầy số 01")
    assert view["current"]["full_no"] == "A-001"
    assert view["waiting_count"] == 1

    ql.finish_current(bid, "Quầy số 01")
    view2 = ql.counter_view(bid, "Quầy số 01")
    assert view2["current"] is None
    assert view2["done_today"] == 1

    called2 = ql.call_next(bid, "Quầy số 01")
    assert called2["full_no"] == "A-002"


def test_call_next_without_waiting_raises(goiso_db):
    branch, ql, _ = goiso_db
    with pytest.raises(ql.QueueError):
        ql.call_next(branch["id"], "Quầy số 01")


def test_daily_limit_enforced(goiso_db):
    branch, ql, db = goiso_db
    bid = branch["id"]
    services = db.get_json_config("services", {}, bid)
    services["B"]["daily_limit"] = 1
    db.set_json_config("services", services, bid)

    ql.issue_ticket(bid, "B")
    with pytest.raises(ql.QueueError):
        ql.issue_ticket(bid, "B")


def test_inactive_service_rejected(goiso_db):
    branch, ql, _ = goiso_db
    with pytest.raises(ql.QueueError):
        ql.issue_ticket(branch["id"], "KHONG_CO")
