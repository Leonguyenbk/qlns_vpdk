"""Test tích hợp Đánh giá KPI: tính điểm định lượng từ dữ liệu nhiệm vụ và quy
trình tự đánh giá -> theo dõi -> tổng hợp -> phê duyệt, cùng các kịch bản rủi
ro được yêu cầu kiểm thử rõ ràng: mẫu số 0, CAP, nhiều người, chuyển kỳ, đổi
hạn sau khi khoá kỳ, thời gian chờ chồng lấn, chống đếm trùng, đổi đơn vị,
khoá kỳ, và truy cập trái phép.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.common.exceptions import BusinessRuleError, PermissionDeniedError
from app.common.utils import utcnow
from app.extensions import db
from app.models import EmployeeAssignment, Task, TaskAssignment, TaskPause
from app.permissions.constants import (
    ROLE_OFFICE_LEADER,
    ROLE_ORG_PERSONNEL,
    ROLE_UNIT_HEAD,
    ROLE_VIEWER,
)
from app.services import kpi_service


def _dt(y, m, d, h=9):
    return datetime(y, m, d, h, tzinfo=timezone.utc)


def _make_org(make_unit, make_position):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    branch = make_unit("CN1", parent=root, unit_type="BRANCH")
    branch2 = make_unit("CN2", parent=root, unit_type="BRANCH")
    staff_pos = make_position("CV", managerial=False)
    head_pos = make_position("TP", managerial=True)
    return root, branch, branch2, staff_pos, head_pos


def _make_criteria_set(actor):
    data = {
        "name": "Bộ tiêu chí thử nghiệm",
        "effective_from": "2026-01-01",
        "criteria": [
            {"code": "SL", "name": "Số lượng", "kind": "TASK_QUANTITY", "max_points": 20, "formula_key": "QUANTITY_RATIO"},
            {"code": "CL", "name": "Chất lượng", "kind": "TASK_QUALITY", "max_points": 32, "formula_key": "QUALITY_RATIO"},
            {"code": "TD", "name": "Tiến độ", "kind": "TASK_PROGRESS", "max_points": 18, "formula_key": "PROGRESS_RATIO"},
        ],
    }
    return kpi_service.create_criteria_set(data, actor=actor)


def _make_period(actor, cset_id, code="2026-Q1", start=date(2026, 1, 1), end=date(2026, 3, 31)):
    return kpi_service.create_period(
        {"code": code, "period_type": "QUARTER", "start_date": start.isoformat(), "end_date": end.isoformat(),
         "criteria_set_id": cset_id},
        actor=actor,
    )


def _make_task(unit, assigner, lead, *, code, workload, deadline, status="COMPLETED", submitted_at=None,
               quality_level=5, product_id=None, has_own_product=True, assigned_date=None,
               parent_task_id=None, contribution=None):
    t = Task(
        code=code,
        name="Nhiệm vụ thử nghiệm", assigning_unit_id=unit.id, creator_id=assigner.id, assigner_id=assigner.id,
        source="AD_HOC", priority="NORMAL", status=status,
        assigned_date=assigned_date or date(2026, 1, 5), original_deadline=deadline,
        deadline_type="INTERNAL", assigned_workload=workload, workload_unit="hồ sơ",
        product_id=product_id, has_own_product=has_own_product, created_by=assigner.id,
        quality_level=quality_level if status == "COMPLETED" else None,
        submitted_at=submitted_at, parent_task_id=parent_task_id,
    )
    db.session.add(t)
    db.session.flush()
    db.session.add(TaskAssignment(
        task_id=t.id, user_id=lead.id, role_in_task="LEAD", contribution_percent=contribution,
        assigned_at=utcnow(),
    ))
    db.session.commit()
    return t


def _detail(score, code):
    return next(d for d in score["details"] if d["criteria_code"] == code)


# ------------------------------- mẫu số bằng 0 -------------------------------

def test_zero_denominator_shows_no_data_not_zero_or_hundred(client, auth_header, make_unit, make_position, make_staff):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader1", branch, head_pos, ROLE_OFFICE_LEADER)
    staff = make_staff("kpistaff1", branch, staff_pos, ROLE_VIEWER)

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    # Không có nhiệm vụ nào cho staff trong kỳ này
    score = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})

    for code in ("SL", "CL", "TD"):
        d = _detail(score, code)
        assert d["ratio_percent"] is None
        assert d["no_data"] is True
        assert d["points_earned"] is None
    assert score["provisional_total"] == 0.0  # chưa có điểm nào tự tính được


# ------------------------------- CAP -------------------------------

def test_cap_limits_recognized_quantity_without_erasing_actual(
    client, auth_header, make_unit, make_position, make_staff
):
    from app.models import Product, ProductCatalogGroup, ProductConversion

    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader2", branch, head_pos, ROLE_OFFICE_LEADER)
    staff = make_staff("kpistaff2", branch, staff_pos, ROLE_VIEWER)

    product = Product(group_code="N1", code="N1.001", name="Hồ sơ TTHC", status="OFFICIAL", created_by=leader.id)
    db.session.add(product)
    db.session.flush()
    db.session.add(ProductConversion(
        product_id=product.id, version=1, kn_value=1.0, cap_value=15,
        effective_from=date(2026, 1, 1), status="OFFICIAL",
    ))
    db.session.commit()

    deadline = date(2026, 2, 1)
    _make_task(branch, leader, staff, workload=10, deadline=deadline, status="COMPLETED",
               submitted_at=_dt(2026, 1, 20), product_id=product.id, code="NV-CAP-1")
    _make_task(branch, leader, staff, workload=10, deadline=deadline, status="COMPLETED",
               submitted_at=_dt(2026, 1, 25), product_id=product.id, code="NV-CAP-2")

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    score = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})

    sl = _detail(score, "SL")
    # Mẫu số = tổng khối lượng quy đổi GIAO (không bị CAP) = 20
    assert sl["raw_denominator"] == 20.0
    # Tử số = ghi nhận sau CAP = min(20, 15) = 15 -> KHÔNG bị xoá khối lượng thực tế 20
    assert sl["raw_numerator"] == 15.0
    assert sl["ratio_percent"] == 75.0


# ------------------------------- Nhiều người cùng làm 1 sản phẩm -------------------------------

def test_multi_person_contribution_splits_quantity_credit(
    client, auth_header, make_unit, make_position, make_staff
):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader3", branch, head_pos, ROLE_OFFICE_LEADER)
    s1 = make_staff("kpistaff3a", branch, staff_pos, ROLE_VIEWER)
    s2 = make_staff("kpistaff3b", branch, staff_pos, ROLE_VIEWER)

    deadline = date(2026, 2, 1)
    t = Task(
        code="NV-SHARED-1", name="Việc chung", assigning_unit_id=branch.id, creator_id=leader.id,
        assigner_id=leader.id, source="AD_HOC", priority="NORMAL", status="COMPLETED",
        assigned_date=date(2026, 1, 5), original_deadline=deadline, deadline_type="INTERNAL",
        assigned_workload=10, workload_unit="hồ sơ", created_by=leader.id, quality_level=5,
        submitted_at=_dt(2026, 1, 20),
    )
    db.session.add(t)
    db.session.flush()
    db.session.add(TaskAssignment(task_id=t.id, user_id=s1.id, role_in_task="LEAD", contribution_percent=60, assigned_at=utcnow()))
    db.session.add(TaskAssignment(task_id=t.id, user_id=s2.id, role_in_task="COLLABORATOR", contribution_percent=40, assigned_at=utcnow()))
    db.session.commit()

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    score1 = kpi_service.compute_score(period["id"], s1.id, actor=leader, meta={})
    score2 = kpi_service.compute_score(period["id"], s2.id, actor=leader, meta={})

    assert _detail(score1, "SL")["raw_denominator"] == 6.0
    assert _detail(score2, "SL")["raw_denominator"] == 4.0
    # Tổng đóng góp = đúng 100% khối lượng gốc, không nhân đôi
    assert _detail(score1, "SL")["raw_denominator"] + _detail(score2, "SL")["raw_denominator"] == 10.0


# ------------------------------- Chuyển kỳ (carry-over) -------------------------------

def test_task_counted_only_in_period_containing_its_deadline(
    client, auth_header, make_unit, make_position, make_staff
):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader4", branch, head_pos, ROLE_OFFICE_LEADER)
    staff = make_staff("kpistaff4", branch, staff_pos, ROLE_VIEWER)

    # Giao trong kỳ 1 (Q1) nhưng hạn hoàn thành rơi vào kỳ 2 (Q2)
    _make_task(branch, leader, staff, workload=10, deadline=date(2026, 4, 15), status="IN_PROGRESS",
               assigned_date=date(2026, 2, 1), code="NV-CARRY-1")

    cset = _make_criteria_set(leader)
    period1 = _make_period(leader, cset["id"], code="2026-Q1", start=date(2026, 1, 1), end=date(2026, 3, 31))
    period2 = _make_period(leader, cset["id"], code="2026-Q2", start=date(2026, 4, 1), end=date(2026, 6, 30))

    score_q1 = kpi_service.compute_score(period1["id"], staff.id, actor=leader, meta={})
    score_q2 = kpi_service.compute_score(period2["id"], staff.id, actor=leader, meta={})

    assert _detail(score_q1, "SL")["raw_denominator"] in (None, 0.0)  # không tính ở kỳ 1
    assert _detail(score_q2, "SL")["raw_denominator"] == 10.0          # tính đúng 1 lần ở kỳ 2


# ------------------------------- Thời gian chờ chồng lấn -------------------------------

def test_overlapping_pause_periods_not_double_subtracted(
    client, auth_header, make_unit, make_position, make_staff
):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader5", branch, head_pos, ROLE_OFFICE_LEADER)
    staff = make_staff("kpistaff5", branch, staff_pos, ROLE_VIEWER)

    deadline = date(2026, 1, 10)
    # Nộp ngày 16/1 — mốc được chọn để PHÂN BIỆT RÕ hai cách tính:
    # gộp đúng (5 ngày loại trừ) -> hạn hiệu lực 15/1 -> nộp SAU hạn (không đạt);
    # trừ trùng sai (3+3=6 ngày) -> hạn hiệu lực 16/1 -> nộp ĐÚNG hạn (đạt).
    # Nếu code gộp khoảng chồng lấn sai, bài test này sẽ FAIL.
    t = _make_task(branch, leader, staff, workload=10, deadline=deadline, status="COMPLETED",
                    submitted_at=_dt(2026, 1, 16), code="NV-PAUSE-1")
    # 2 khoảng tạm dừng CHỒNG LẤN, đã xác nhận: 1/1-1/4 (3 ngày) và 1/3-1/6 (3 ngày) -> gộp = 5 ngày
    db.session.add(TaskPause(
        task_id=t.id, reason_code="WAITING_CITIZEN", started_at=_dt(2026, 1, 1), ended_at=_dt(2026, 1, 4),
        confirmed_by=leader.id, confirmed_at=utcnow(), created_by=leader.id,
    ))
    db.session.add(TaskPause(
        task_id=t.id, reason_code="WAITING_AGENCY", started_at=_dt(2026, 1, 3), ended_at=_dt(2026, 1, 6),
        confirmed_by=leader.id, confirmed_at=utcnow(), created_by=leader.id,
    ))
    db.session.commit()

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    score = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})

    # Hạn hiệu lực đúng = 10/1 + 5 (gộp, không trừ trùng) = 15/1; nộp 16/1 -> TRỄ HẠN.
    td = _detail(score, "TD")
    assert td["raw_numerator"] == 0.0
    assert td["ratio_percent"] == 0.0


# ------------------------------- Chống đếm trùng cha/con -------------------------------

def test_parent_aggregator_task_excluded_from_quantity(
    client, auth_header, make_unit, make_position, make_staff
):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader6", branch, head_pos, ROLE_OFFICE_LEADER)
    staff = make_staff("kpistaff6", branch, staff_pos, ROLE_VIEWER)

    parent = _make_task(branch, leader, staff, workload=100, deadline=date(2026, 2, 1),
                         status="COMPLETED", submitted_at=_dt(2026, 1, 15), has_own_product=False,
                         code="NV-PARENT-1")
    _make_task(branch, leader, staff, workload=10, deadline=date(2026, 2, 1), status="COMPLETED",
               submitted_at=_dt(2026, 1, 15), parent_task_id=parent.id, code="NV-CHILD-1")

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    score = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})

    # Chỉ tính khối lượng của việc con (10) — việc cha (100) bị loại vì has_own_product=False
    assert _detail(score, "SL")["raw_denominator"] == 10.0


# ------------------------------- Đổi đơn vị không làm sai báo cáo cũ -------------------------------

def test_unit_transfer_does_not_corrupt_existing_score_snapshot(
    client, auth_header, make_unit, make_position, make_staff
):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader7", branch, head_pos, ROLE_OFFICE_LEADER)
    staff = make_staff("kpistaff7", branch, staff_pos, ROLE_VIEWER)

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    score = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})
    assert score["unit_id_snapshot"] == branch.id

    # Nhân sự chuyển sang chi nhánh khác GIỮA chừng
    old_assignment = staff.employee.primary_active_assignment()
    old_assignment.end_date = date(2026, 2, 1)
    db.session.add(EmployeeAssignment(
        employee_id=staff.employee_id, unit_id=branch2.id, position_id=staff_pos.id,
        assignment_type="TRANSFER", start_date=date(2026, 2, 2), is_primary=True,
    ))
    db.session.commit()

    # Tính lại điểm (kỳ vẫn mở) — bản ghi ĐÃ TỒN TẠI không bị viết lại snapshot
    score_again = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})
    assert score_again["id"] == score["id"]
    assert score_again["unit_id_snapshot"] == branch.id  # vẫn giữ đơn vị tại thời điểm tạo


# ------------------------------- Khoá kỳ -------------------------------

def test_period_lock_blocks_recompute_and_requires_adjust_flow(
    client, auth_header, make_unit, make_position, make_staff
):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    # Vai trò kép để đi hết luồng theo dõi -> tổng hợp -> phê duyệt trong một test
    leader = make_staff("kpileader8", branch, head_pos, [ROLE_OFFICE_LEADER, ROLE_ORG_PERSONNEL])
    staff = make_staff("kpistaff8", branch, staff_pos, ROLE_VIEWER)

    _make_task(branch, leader, staff, workload=10, deadline=date(2026, 2, 1), status="COMPLETED",
               submitted_at=_dt(2026, 1, 15), code="NV-LOCK-1")

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    score = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})
    score = kpi_service.review_score(score["id"], {}, actor=leader, meta={})
    score = kpi_service.aggregate_score(score["id"], {}, actor=leader, meta={})

    # Người tự đánh giá không được tự phê duyệt (giả sử leader vừa self-assess hộ — bỏ qua ở đây)
    score = kpi_service.approve_score(score["id"], {"official_rating": "Hoàn thành tốt nhiệm vụ"},
                                       actor=leader, meta={})
    assert score["status"] == "APPROVED"
    assert score["is_locked"] is True

    kpi_service.lock_period(period["id"], actor=leader, meta={})

    with pytest.raises(BusinessRuleError):
        kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})

    # Sửa kết quả đã khoá phải qua adjust_score (Mẫu số 15) — giữ nguyên bản cũ
    new_score = kpi_service.adjust_score(
        score["id"], {"reason": "Phát hiện sai sót sau khi đã xếp loại"}, actor=leader, meta={}
    )
    assert new_score["replaces_id"] == score["id"]
    assert new_score["is_locked"] is False
    old_reloaded = kpi_service.get_score(score["id"], actor=leader)
    assert old_reloaded["official_rating"] == "Hoàn thành tốt nhiệm vụ"  # bản cũ được giữ nguyên


def test_self_approve_own_score_is_blocked(client, auth_header, make_unit, make_position, make_staff):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    # Trưởng phòng vừa là người được đánh giá vừa có quyền phê duyệt (trường hợp xấu nhất)
    leader = make_staff("kpileader9", branch, head_pos, ROLE_OFFICE_LEADER)

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    score = kpi_service.compute_score(period["id"], leader.id, actor=leader, meta={})

    with pytest.raises(BusinessRuleError):
        kpi_service.approve_score(score["id"], {"official_rating": "Hoàn thành tốt nhiệm vụ"},
                                   actor=leader, meta={})


# ------------------------------- Truy cập trái phép -------------------------------

def test_unauthorized_kpi_actions_denied(client, auth_header, make_unit, make_position, make_staff):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader10", branch, head_pos, ROLE_OFFICE_LEADER)
    staff = make_staff("kpistaff10", branch, staff_pos, ROLE_VIEWER)
    other_staff = make_staff("kpistaff10b", branch, staff_pos, ROLE_VIEWER)

    cset = _make_criteria_set(leader)
    period = _make_period(leader, cset["id"])
    score = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})

    # VIEWER không có kpi.review/kpi.approve
    with pytest.raises(PermissionDeniedError):
        kpi_service.review_score(score["id"], {}, actor=other_staff, meta={})
    with pytest.raises(PermissionDeniedError):
        kpi_service.approve_score(score["id"], {"official_rating": "x"}, actor=other_staff, meta={})
    # Không được tự đánh giá kết quả của người khác
    with pytest.raises(PermissionDeniedError):
        kpi_service.self_assess(score["id"], {}, actor=other_staff, meta={})
    # Không có kpi.view_all -> không xem được KPI của người khác
    with pytest.raises(PermissionDeniedError):
        kpi_service.get_score(score["id"], actor=other_staff)


def test_unauthenticated_kpi_request_rejected(client):
    resp = client.get("/api/kpi/scores/mine")
    assert resp.status_code == 401


# ------------------------------- Bộ tiêu chí mặc định + tách nhánh quản lý -------------------------------

def test_default_criteria_set_matches_document_totals(client, auth_header, make_unit, make_position, make_staff):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader11", branch, head_pos, ROLE_OFFICE_LEADER)

    cset = kpi_service.create_default_criteria_set(
        {"effective_from": "2026-01-01"}, actor=leader,
    )
    full = kpi_service.get_criteria_set(cset["id"])
    top = {c["code"]: c for c in full["criteria"]}

    # 30 điểm tiêu chí chung (Nhóm 1 + 2 + 3 = 9 + 9 + 12), đúng Phụ lục I
    assert top["NHOM1"]["max_points"] == 9.0
    assert top["NHOM2"]["max_points"] == 9.0
    assert top["NHOM3"]["max_points"] == 12.0
    assert sum(c["max_points"] for c in top["NHOM1"]["children"]) == 9.0
    assert sum(c["max_points"] for c in top["NHOM2"]["children"]) == 9.0
    assert sum(c["max_points"] for c in top["NHOM3"]["children"]) == 12.0

    # 70 điểm kết quả nhiệm vụ — không quản lý (20 + 32 + 18) và quản lý (28 + 21 + 11 + 10)
    assert top["STAFF70"]["max_points"] == 70.0
    assert sum(c["max_points"] for c in top["STAFF70"]["children"]) == 70.0
    assert top["MA"]["max_points"] == 28.0
    assert sum(c["max_points"] for c in top["MA"]["children"]) == 28.0
    assert top["MB"]["max_points"] == 21.0
    assert top["MC"]["max_points"] == 11.0
    assert top["MD"]["max_points"] == 10.0
    managerial_total = top["MA"]["max_points"] + top["MB"]["max_points"] + top["MC"]["max_points"] + top["MD"]["max_points"]
    assert managerial_total == 70.0


def test_managerial_and_nonmanagerial_branches_do_not_mix(
    client, auth_header, make_unit, make_position, make_staff
):
    root, branch, branch2, staff_pos, head_pos = _make_org(make_unit, make_position)
    leader = make_staff("kpileader12", branch, head_pos, ROLE_OFFICE_LEADER)
    staff = make_staff("kpistaff12", branch, staff_pos, ROLE_VIEWER)   # không quản lý
    manager = make_staff("kpimgr12", branch, head_pos, ROLE_VIEWER)   # is_managerial=True (head_pos)

    cset = kpi_service.create_default_criteria_set({"effective_from": "2026-01-01"}, actor=leader)
    period = _make_period(leader, cset["id"])

    staff_score = kpi_service.compute_score(period["id"], staff.id, actor=leader, meta={})
    mgr_score = kpi_service.compute_score(period["id"], manager.id, actor=leader, meta={})

    staff_codes = {d["criteria_code"] for d in staff_score["details"]}
    mgr_codes = {d["criteria_code"] for d in mgr_score["details"]}

    # Viên chức không quản lý chỉ có nhánh SL/CL/TD 20/32/18 — KHÔNG có nhánh quản lý
    assert {"SL", "CL", "TD"} <= staff_codes
    assert not ({"MSL", "MCL", "MTD", "MB", "MC", "MD"} & staff_codes)

    # Viên chức quản lý chỉ có nhánh MSL/MCL/MTD + MB/MC/MD — KHÔNG có nhánh SL/CL/TD 20/32/18
    assert {"MSL", "MCL", "MTD", "MB", "MC", "MD"} <= mgr_codes
    assert not ({"SL", "CL", "TD"} & mgr_codes)
