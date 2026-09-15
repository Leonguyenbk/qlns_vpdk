"""Test module Khảo sát – Đánh giá mức độ hài lòng."""
from __future__ import annotations


def _create_survey(client, headers, title="Khảo sát hài lòng"):
    resp = client.post("/api/surveys", headers=headers, json={"title": title})
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["data"]


def _add_choice_question(client, headers, survey_id, text="Anh/chị đánh giá thái độ phục vụ?"):
    resp = client.post(
        f"/api/surveys/{survey_id}/questions",
        headers=headers,
        json={
            "question_text": text,
            "question_type": "single_choice",
            "is_required": True,
            "options": [
                {"option_text": "Hài lòng"},
                {"option_text": "Không hài lòng"},
            ],
        },
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["data"]


def test_full_flow_create_publish_submit_view_results(client, admin_user, auth_header, make_unit):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    survey_id = survey["id"]
    assert survey["status"] == "draft"

    # Thêm 5 câu hỏi đủ loại
    q1 = _add_choice_question(client, headers, survey_id)
    q2 = client.post(
        f"/api/surveys/{survey_id}/questions",
        headers=headers,
        json={"question_text": "Đánh giá thời gian xử lý?", "question_type": "rating", "is_required": True},
    ).get_json()["data"]
    client.post(
        f"/api/surveys/{survey_id}/questions",
        headers=headers,
        json={"question_text": "Anh/chị có hài lòng chung không?", "question_type": "yes_no"},
    )
    client.post(
        f"/api/surveys/{survey_id}/questions",
        headers=headers,
        json={"question_text": "Ý kiến góp ý khác", "question_type": "textarea"},
    )
    client.post(
        f"/api/surveys/{survey_id}/questions",
        headers=headers,
        json={"question_text": "Số lần đến giao dịch trong năm?", "question_type": "number"},
    )

    questions = client.get(f"/api/surveys/{survey_id}/questions", headers=headers).get_json()["data"]
    assert len(questions) == 5

    # Đổi thứ tự: đưa câu cuối lên đầu
    reorder_items = [{"id": q["id"], "sort_order": i} for i, q in enumerate(reversed(questions))]
    resp = client.post(
        f"/api/surveys/{survey_id}/questions/reorder", headers=headers, json={"items": reorder_items}
    )
    assert resp.status_code == 200
    reordered = resp.get_json()["data"]
    assert reordered[0]["id"] == questions[-1]["id"]

    # Xuất bản
    resp = client.post(f"/api/surveys/{survey_id}/status", headers=headers, json={"status": "active"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "active"

    # Người dân mở link công khai theo slug
    public = client.get(f"/api/public/surveys/{survey['slug']}").get_json()["data"]
    assert public["available"] is True
    assert len(public["questions"]) == 5

    # Gửi đánh giá
    q1_options = next(q for q in public["questions"] if q["id"] == q1["id"])["options"]
    submit_payload = {
        "answers": [
            {"question_id": q1["id"], "option_id": q1_options[0]["id"]},
            {"question_id": q2["id"], "answer_number": 5},
        ]
    }
    resp = client.post(f"/api/public/surveys/{survey_id}/submit", json=submit_payload)
    assert resp.status_code == 201, resp.get_json()

    # Admin xem kết quả
    responses = client.get(f"/api/surveys/{survey_id}/responses", headers=headers).get_json()["data"]
    assert responses["pagination"]["total"] == 1

    stats = client.get(f"/api/surveys/{survey_id}/statistics", headers=headers).get_json()["data"]
    assert stats["overview"]["total_responses"] == 1
    assert stats["overview"]["average_score"] == 5.0


def test_public_payload_lists_branches_and_accepts_respondent_contact(
    client, admin_user, auth_header, make_unit
):
    headers = auth_header("admin_test")
    branch = make_unit("KS-BRANCH", name="CN Khảo sát", unit_type="BRANCH")
    survey = _create_survey(client, headers)
    q = _add_choice_question(client, headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})

    public = client.get(f"/api/public/surveys/{survey['slug']}").get_json()["data"]
    assert {"id": branch.id, "code": branch.code, "name": branch.name} in public["branches"]

    opt_id = q["options"][0]["id"]
    resp = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={
            "branch_id": branch.id,
            "respondent_name": "Nguyễn Văn A",
            "respondent_phone": "0905123456",
            "respondent_email": "a@example.com",
            "respondent_address": "123 Lê Duẩn",
            "answers": [{"question_id": q["id"], "option_id": opt_id}],
        },
    )
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()["data"]
    assert data["branch_id"] == branch.id
    assert data["respondent_email"] == "a@example.com"
    assert data["respondent_address"] == "123 Lê Duẩn"

    bad_email = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"respondent_email": "not-an-email", "answers": [{"question_id": q["id"], "option_id": opt_id}]},
    )
    assert bad_email.status_code == 422


def test_edit_question_after_response_creates_revision_and_preserves_history(
    client, admin_user, auth_header
):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    q = _add_choice_question(client, headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})

    opt_id = q["options"][0]["id"]
    client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": q["id"], "option_id": opt_id}]},
    )

    # Sửa nội dung câu hỏi đã có phản hồi -> phải tạo bản ghi mới, không ghi đè
    resp = client.put(
        f"/api/survey-questions/{q['id']}",
        headers=headers,
        json={"question_text": "Câu hỏi đã đổi nội dung hoàn toàn khác"},
    )
    assert resp.status_code == 200
    revised = resp.get_json()["data"]
    assert revised["revised_from_id"] == q["id"]
    assert revised["id"] != q["id"]

    # Câu hỏi cũ vẫn còn nguyên nội dung gốc để không làm sai lệch thống kê lịch sử
    old_questions = client.get(
        f"/api/surveys/{survey['id']}/questions?include_inactive=1", headers=headers
    ).get_json()["data"]
    old = next(x for x in old_questions if x["id"] == q["id"])
    assert old["question_text"] == q["question_text"]
    assert old["is_active"] is False

    stats = client.get(f"/api/surveys/{survey['id']}/statistics", headers=headers).get_json()["data"]
    # Câu hỏi cũ (đã ẩn) không còn trong by_question (chỉ liệt kê câu đang hoạt động)
    active_ids = {item["id"] for item in stats["by_question"]}
    assert q["id"] not in active_ids
    assert revised["id"] in active_ids


def test_required_question_left_blank_is_rejected(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    q = _add_choice_question(client, headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})

    resp = client.post(f"/api/public/surveys/{survey['id']}/submit", json={"answers": []})
    assert resp.status_code == 422
    assert q["question_text"] in resp.get_json()["message"]


def test_multiple_choice_saved_and_counted_correctly(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    q = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Anh/chị biết đến dịch vụ qua kênh nào?",
            "question_type": "multiple_choice",
            "options": [{"option_text": "Facebook"}, {"option_text": "Bạn bè"}, {"option_text": "Khác"}],
        },
    ).get_json()["data"]
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})

    opt_ids = [o["id"] for o in q["options"][:2]]
    resp = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": q["id"], "option_ids": opt_ids}]},
    )
    assert resp.status_code == 201

    stats = client.get(f"/api/surveys/{survey['id']}/statistics", headers=headers).get_json()["data"]
    q_stats = next(item for item in stats["by_question"] if item["id"] == q["id"])["stats"]
    counted = {o["option_id"]: o["count"] for o in q_stats["options"]}
    assert counted[opt_ids[0]] == 1
    assert counted[opt_ids[1]] == 1


def test_filter_dashboard_by_date_range(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    q = _add_choice_question(client, headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})
    client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": q["id"], "option_id": q["options"][0]["id"]}]},
    )

    stats = client.get(
        f"/api/surveys/{survey['id']}/statistics?preset=today", headers=headers
    ).get_json()["data"]
    assert stats["overview"]["total_responses"] == 1

    from datetime import date, timedelta

    yesterday = (date.today() - timedelta(days=2)).isoformat()
    day_before = (date.today() - timedelta(days=5)).isoformat()
    stats_old_range = client.get(
        f"/api/surveys/{survey['id']}/statistics?date_from={day_before}&date_to={yesterday}",
        headers=headers,
    ).get_json()["data"]
    assert stats_old_range["overview"]["total_responses"] == 0


def test_duplicate_submit_with_same_client_token_is_idempotent(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    q = _add_choice_question(client, headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})

    payload = {
        "client_token": "tok-123",
        "answers": [{"question_id": q["id"], "option_id": q["options"][0]["id"]}],
    }
    r1 = client.post(f"/api/public/surveys/{survey['id']}/submit", json=payload)
    r2 = client.post(f"/api/public/surveys/{survey['id']}/submit", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.get_json()["data"]["id"] == r2.get_json()["data"]["id"]

    total = client.get(f"/api/surveys/{survey['id']}/responses", headers=headers).get_json()["data"][
        "pagination"
    ]["total"]
    assert total == 1


def test_cannot_submit_to_draft_or_closed_survey(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    q = _add_choice_question(client, headers, survey["id"])

    resp = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": q["id"], "option_id": q["options"][0]["id"]}]},
    )
    assert resp.status_code == 400  # còn draft

    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "closed"})
    resp = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": q["id"], "option_id": q["options"][0]["id"]}]},
    )
    assert resp.status_code == 400


def test_delete_survey_blocked_once_it_has_responses(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    q = _add_choice_question(client, headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})
    client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": q["id"], "option_id": q["options"][0]["id"]}]},
    )

    resp = client.delete(f"/api/surveys/{survey['id']}", headers=headers)
    assert resp.status_code == 409


def test_missing_permission_is_forbidden(client, make_user, auth_header):
    make_user("viewer_only", role_code="VIEWER")
    headers = auth_header("viewer_only")
    resp = client.post("/api/surveys", headers=headers, json={"title": "X"})
    assert resp.status_code == 403


def test_survey_editor_role_can_edit_but_not_delete_or_export(client, admin_user, auth_header, make_user):
    make_user("survey_editor_test", role_code="SURVEY_EDITOR")
    editor_headers = auth_header("survey_editor_test")

    created = client.post(
        "/api/surveys",
        headers=editor_headers,
        json={"title": "Khảo sát do biên tập viên tạo"},
    )
    assert created.status_code == 201, created.get_json()
    survey = created.get_json()["data"]

    question = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=editor_headers,
        json={"question_text": "Bạn hài lòng chứ?", "question_type": "yes_no"},
    )
    assert question.status_code == 201, question.get_json()

    stats = client.get(f"/api/surveys/{survey['id']}/responses", headers=editor_headers)
    assert stats.status_code == 200

    assert client.delete(f"/api/surveys/{survey['id']}", headers=editor_headers).status_code == 403
    assert client.get(f"/api/surveys/{survey['id']}/export", headers=editor_headers).status_code == 403


def test_office_leader_can_view_stats_but_not_create_or_edit_surveys(
    client, admin_user, auth_header, make_user
):
    admin_headers = auth_header("admin_test")
    survey = _create_survey(client, admin_headers)
    _add_choice_question(client, admin_headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=admin_headers, json={"status": "active"})

    make_user("office_leader_test", role_code="OFFICE_LEADER")
    leader_headers = auth_header("office_leader_test")

    assert client.get(f"/api/surveys/{survey['id']}", headers=leader_headers).status_code == 200
    assert client.get(
        f"/api/surveys/{survey['id']}/responses", headers=leader_headers
    ).status_code == 200
    assert client.get(
        f"/api/surveys/{survey['id']}/statistics", headers=leader_headers
    ).status_code == 200

    assert client.post("/api/surveys", headers=leader_headers, json={"title": "X"}).status_code == 403
    assert client.put(
        f"/api/surveys/{survey['id']}", headers=leader_headers, json={"title": "Y"}
    ).status_code == 403
    assert client.delete(f"/api/surveys/{survey['id']}", headers=leader_headers).status_code == 403
    assert client.get(f"/api/surveys/{survey['id']}/export", headers=leader_headers).status_code == 403


def test_single_choice_requires_at_least_two_options(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    resp = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Câu hỏi thiếu phương án",
            "question_type": "single_choice",
            "options": [{"option_text": "Chỉ một"}],
        },
    )
    assert resp.status_code == 422


def test_publish_requires_at_least_one_active_question(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers)
    resp = client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})
    assert resp.status_code == 422
