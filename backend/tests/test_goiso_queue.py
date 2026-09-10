"""Test nghiệp vụ hàng đợi của module goiso (cấp số / gọi số / hoàn thành).

Chạy trực tiếp trên một file SQLite tạm — goiso hiện chưa dùng SQLAlchemy
(sẽ chuyển ở Phase 6). Bao phủ yêu cầu mục 20: tạo ticket, gọi số, hoàn thành số.
"""
from __future__ import annotations

import importlib

import pytest

from app.modules.goiso import legacy_db


@pytest.fixture
def goiso_db(tmp_path, monkeypatch):
    """Trỏ legacy_db sang file SQLite tạm và khởi tạo schema."""
    db_file = tmp_path / "goiso_test.db"
    monkeypatch.setattr(legacy_db, "DB_PATH", str(db_file))
    legacy_db._invalidate_branch_cache()
    legacy_db.init_db()

    ql = importlib.import_module("app.modules.goiso.queue_logic")

    branch = legacy_db.create_branch("t1", "Test", "Chi nhánh Test")
    # Tắt khoá giờ để test không phụ thuộc thời điểm chạy
    legacy_db.set_json_config("extra", {"lock_time_enabled": False}, branch["id"])
    yield branch, ql, legacy_db
    legacy_db._invalidate_branch_cache()


def test_issue_call_finish_flow(goiso_db):
    branch, ql, db = goiso_db
    bid = branch["id"]

    t1 = ql.issue_ticket(bid, "A")
    t2 = ql.issue_ticket(bid, "A")
    assert (t1["number"], t2["number"]) == (1, 2)
    assert t1["full_no"] == "A-001"

    # "Quầy số 01" phục vụ prefix A theo cấu hình mặc định
    called = ql.call_next(bid, "Quầy số 01", staff_name="NV Test")
    assert called["full_no"] == "A-001"
    assert called["counter_id"] == "Quầy số 01"

    view = ql.counter_view(bid, "Quầy số 01")
    assert view["current"]["full_no"] == "A-001"
    assert view["waiting_count"] == 1  # còn A-002

    ql.finish_current(bid, "Quầy số 01")
    view2 = ql.counter_view(bid, "Quầy số 01")
    assert view2["current"] is None
    assert view2["done_today"] == 1

    # Gọi tiếp -> A-002
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
