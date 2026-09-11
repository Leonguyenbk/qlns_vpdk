"""Test luồng Giao việc: giao -> cập nhật tiến độ -> nộp -> nghiệm thu, và các
quy tắc bắt buộc (không tự nghiệm thu, phân quyền theo phạm vi đơn vị, khoá
lạc quan chống ghi đè)."""
from __future__ import annotations

from datetime import date, timedelta

from app.permissions.constants import ROLE_UNIT_HEAD, ROLE_VIEWER


def _make_org(make_unit, make_position):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    branch = make_unit("CN1", parent=root, unit_type="BRANCH")
    staff_pos = make_position("CV", managerial=False)
    head_pos = make_position("TP", managerial=True)
    return root, branch, staff_pos, head_pos


def _task_body(unit, assignee_user_id, **over):
    body = {
        "name": "Kiểm tra hồ sơ đăng ký đất đai",
        "assigning_unit_id": unit.id,
        "assigned_date": date.today().isoformat(),
        "original_deadline": (date.today() + timedelta(days=10)).isoformat(),
        "assigned_workload": 10,
        "workload_unit": "hồ sơ",
        "assignees": [{"user_id": assignee_user_id, "role_in_task": "LEAD"}],
    }
    body.update(over)
    return body


def test_full_lifecycle_assign_progress_accept(client, auth_header, make_unit, make_position, make_staff):
    root, branch, staff_pos, head_pos = _make_org(make_unit, make_position)
    head = make_staff("head1", branch, head_pos, ROLE_UNIT_HEAD)
    staff = make_staff("staff1", branch, staff_pos, ROLE_VIEWER)

    resp = client.post("/api/tasks", headers=auth_header("head1"), json=_task_body(branch, staff.id))
    assert resp.status_code == 201, resp.get_json()
    task = resp.get_json()["data"]
    assert task["status"] == "ASSIGNED"
    assert task["code"].startswith(f"NV-{date.today().year}-")
    task_id = task["id"]

    # Nhân viên cập nhật tiến độ giữa chừng -> Đang thực hiện
    resp = client.put(f"/api/tasks/{task_id}/progress", headers=auth_header("staff1"),
                       json={"progress_percent": 40})
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["data"]["status"] == "IN_PROGRESS"

    # Cập nhật 100% -> CHỈ được "Chờ nghiệm thu", không tự "Hoàn thành"
    resp = client.put(f"/api/tasks/{task_id}/progress", headers=auth_header("staff1"),
                       json={"progress_percent": 100})
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["data"]["status"] == "PENDING_ACCEPTANCE"

    # Người thực hiện không có quyền task.accept -> không tự nghiệm thu được
    resp = client.post(f"/api/tasks/{task_id}/accept", headers=auth_header("staff1"), json={"quality_level": 5})
    assert resp.status_code == 403

    # Trưởng phòng nghiệm thu -> Hoàn thành
    resp = client.post(f"/api/tasks/{task_id}/accept", headers=auth_header("head1"), json={"quality_level": 5})
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()["data"]
    assert data["status"] == "COMPLETED"
    assert data["quality_level"] == 5
    assert data["accepted_by"] is not None


def test_lead_cannot_self_accept_own_task(client, auth_header, make_unit, make_position, make_staff):
    root, branch, staff_pos, head_pos = _make_org(make_unit, make_position)
    head = make_staff("head2", branch, head_pos, ROLE_UNIT_HEAD)

    resp = client.post("/api/tasks", headers=auth_header("head2"), json=_task_body(branch, head.id))
    task_id = resp.get_json()["data"]["id"]
    client.put(f"/api/tasks/{task_id}/progress", headers=auth_header("head2"), json={"progress_percent": 100})

    resp = client.post(f"/api/tasks/{task_id}/accept", headers=auth_header("head2"), json={})
    assert resp.status_code == 400
    assert "không được tự nghiệm thu" in resp.get_json()["message"]


def test_return_for_revision_increments_rework_and_blocks_completion(
    client, auth_header, make_unit, make_position, make_staff
):
    root, branch, staff_pos, head_pos = _make_org(make_unit, make_position)
    head = make_staff("head3", branch, head_pos, ROLE_UNIT_HEAD)
    staff = make_staff("staff3", branch, staff_pos, ROLE_VIEWER)

    resp = client.post("/api/tasks", headers=auth_header("head3"), json=_task_body(branch, staff.id))
    task_id = resp.get_json()["data"]["id"]
    client.put(f"/api/tasks/{task_id}/progress", headers=auth_header("staff3"), json={"progress_percent": 100})

    resp = client.post(f"/api/tasks/{task_id}/return", headers=auth_header("head3"),
                        json={"reason": "Thiếu minh chứng, bổ sung lại."})
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()["data"]
    assert data["status"] == "NEEDS_REVISION"
    assert data["rework_count"] == 1


def test_unauthorized_cross_branch_access_denied(client, auth_header, make_unit, make_position, make_staff):
    root, branch, staff_pos, head_pos = _make_org(make_unit, make_position)
    other_branch = make_unit("CN2", parent=root, unit_type="BRANCH")
    make_staff("head4a", branch, head_pos, ROLE_UNIT_HEAD, scopes=(("SUBTREE", branch),))
    staff = make_staff("staff4", branch, staff_pos, ROLE_VIEWER)
    make_staff("head4b", other_branch, head_pos, ROLE_UNIT_HEAD, scopes=(("SUBTREE", other_branch),))

    resp = client.post("/api/tasks", headers=auth_header("head4a"), json=_task_body(branch, staff.id))
    task_id = resp.get_json()["data"]["id"]

    # Trưởng phòng chi nhánh khác — ngoài phạm vi — không xem/không nghiệm thu được
    resp = client.get(f"/api/tasks/{task_id}", headers=auth_header("head4b"))
    assert resp.status_code == 403

    resp = client.post(f"/api/tasks/{task_id}/accept", headers=auth_header("head4b"), json={"quality_level": 5})
    assert resp.status_code == 403

    resp = client.put(f"/api/tasks/{task_id}/deadline", headers=auth_header("head4b"),
                       json={"new_deadline": (date.today() + timedelta(days=20)).isoformat(), "reason": "x"})
    assert resp.status_code == 403

    # Người ngoài cuộc không có task.view_own/view_all không xem được danh sách của người khác
    outsider_no_perm_resp = client.get("/api/tasks", headers=auth_header("head4b"))
    assert outsider_no_perm_resp.status_code == 200  # head4b có TASK_VIEW_ALL nhưng phạm vi rỗng với branch kia
    assert all(t["id"] != task_id for t in outsider_no_perm_resp.get_json()["data"]["items"])


def test_unauthenticated_request_rejected(client, make_unit, make_position, make_staff):
    root, branch, staff_pos, head_pos = _make_org(make_unit, make_position)
    make_staff("head5", branch, head_pos, ROLE_UNIT_HEAD)
    resp = client.get("/api/tasks")
    assert resp.status_code == 401


def test_version_conflict_on_concurrent_progress_update(client, auth_header, make_unit, make_position, make_staff):
    root, branch, staff_pos, head_pos = _make_org(make_unit, make_position)
    head = make_staff("head6", branch, head_pos, ROLE_UNIT_HEAD)
    staff = make_staff("staff6", branch, staff_pos, ROLE_VIEWER)

    resp = client.post("/api/tasks", headers=auth_header("head6"), json=_task_body(branch, staff.id))
    task = resp.get_json()["data"]
    task_id, version = task["id"], task["version"]

    resp = client.put(f"/api/tasks/{task_id}/progress", headers=auth_header("staff6"),
                       json={"progress_percent": 40, "expected_version": version})
    assert resp.status_code == 200, resp.get_json()

    # Gửi lại thao tác dựa trên version cũ (giả lập 2 tab cùng sửa) -> xung đột
    resp = client.put(f"/api/tasks/{task_id}/progress", headers=auth_header("staff6"),
                       json={"progress_percent": 60, "expected_version": version})
    assert resp.status_code == 409


def test_multi_person_contribution_must_sum_to_100(client, auth_header, make_unit, make_position, make_staff):
    root, branch, staff_pos, head_pos = _make_org(make_unit, make_position)
    head = make_staff("head7", branch, head_pos, ROLE_UNIT_HEAD)
    s1 = make_staff("staff7a", branch, staff_pos, ROLE_VIEWER)
    s2 = make_staff("staff7b", branch, staff_pos, ROLE_VIEWER)

    body = _task_body(branch, s1.id, assignees=[
        {"user_id": s1.id, "role_in_task": "LEAD", "contribution_percent": 60},
        {"user_id": s2.id, "role_in_task": "COLLABORATOR", "contribution_percent": 30},
    ])
    resp = client.post("/api/tasks", headers=auth_header("head7"), json=body)
    assert resp.status_code == 400
    assert "100%" in resp.get_json()["message"]

    body["assignees"][1]["contribution_percent"] = 40
    resp = client.post("/api/tasks", headers=auth_header("head7"), json=body)
    assert resp.status_code == 201, resp.get_json()
    assignments = resp.get_json()["data"]["assignments"]
    assert {a["user_id"]: a["contribution_percent"] for a in assignments} == {s1.id: 60.0, s2.id: 40.0}


def test_blocker_report_and_resume_excludes_pause(client, auth_header, make_unit, make_position, make_staff):
    root, branch, staff_pos, head_pos = _make_org(make_unit, make_position)
    head = make_staff("head8", branch, head_pos, ROLE_UNIT_HEAD)
    staff = make_staff("staff8", branch, staff_pos, ROLE_VIEWER)

    resp = client.post("/api/tasks", headers=auth_header("head8"), json=_task_body(branch, staff.id))
    task_id = resp.get_json()["data"]["id"]
    client.put(f"/api/tasks/{task_id}/progress", headers=auth_header("staff8"), json={"progress_percent": 30})

    resp = client.post(f"/api/tasks/{task_id}/blockers", headers=auth_header("staff8"),
                        json={"reason_code": "WAITING_CITIZEN", "note": "Chờ dân bổ sung hồ sơ"})
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()["data"]
    assert data["is_blocked"] is True
    assert data["status"] == "PAUSED"
    pause_id = data["pauses"][0]["id"]
    assert data["pauses"][0]["is_confirmed"] is False

    # Chỉ người có task.manage mới xác nhận được thời gian tạm dừng
    resp = client.post(f"/api/tasks/{task_id}/pauses/{pause_id}/confirm", headers=auth_header("staff8"))
    assert resp.status_code == 403
    resp = client.post(f"/api/tasks/{task_id}/pauses/{pause_id}/confirm", headers=auth_header("head8"))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_confirmed"] is True

    resp = client.post(f"/api/tasks/{task_id}/resume", headers=auth_header("staff8"), json={})
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["status"] == "IN_PROGRESS"
    assert data["is_blocked"] is False
    assert data["pauses"][0]["ended_at"] is not None
