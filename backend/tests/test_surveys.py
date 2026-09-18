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
    assert {"id": branch.id, "code": branch.code, "name": branch.name, "full": False} in public["branches"]

    opt_id = q["options"][0]["id"]
    resp = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={
            "branch_id": branch.id,
            "respondent_name": "Nguyễn Văn A",
            "respondent_phone": "0905123456",
            "respondent_id_number": "012345678901",
            "respondent_address": "123 Lê Duẩn",
            "answers": [{"question_id": q["id"], "option_id": opt_id}],
        },
    )
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()["data"]
    assert data["branch_id"] == branch.id
    assert data["respondent_id_number"] == "012345678901"
    assert data["respondent_address"] == "123 Lê Duẩn"

    bad_id_number = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"respondent_id_number": "12345", "answers": [{"question_id": q["id"], "option_id": opt_id}]},
    )
    assert bad_id_number.status_code == 422


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


def test_conditional_question_is_required_only_when_triggered_and_scores_child(
    client, admin_user, auth_header
):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers, title="Khảo sát có câu hỏi phụ")
    parent = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Hồ sơ có xử lý đúng hạn không?",
            "question_type": "yes_no",
            "is_required": True,
            "yes_score": 10,
        },
    ).get_json()["data"]
    child_response = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Nếu không, nguyên nhân là gì?",
            "question_type": "single_choice",
            "is_required": True,
            "parent_question_id": parent["id"],
            "trigger_answer": "no",
            "options": [
                {"option_text": "Thiếu giấy tờ", "score": 4},
                {"option_text": "Lý do khác", "score": 1},
            ],
        },
    )
    assert child_response.status_code == 201, child_response.get_json()
    child = child_response.get_json()["data"]
    client.post(
        f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"}
    )

    public = client.get(f"/api/public/surveys/{survey['slug']}").get_json()["data"]
    public_child = next(q for q in public["questions"] if q["id"] == child["id"])
    assert public_child["parent_question_id"] == parent["id"]
    assert public_child["trigger_answer"] == "no"
    assert "max_score" not in public_child

    yes_response = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": parent["id"], "answer_text": "yes"}]},
    )
    assert yes_response.status_code == 201, yes_response.get_json()
    assert len(yes_response.get_json()["data"]["answers"]) == 1

    missing_child = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": parent["id"], "answer_text": "no"}]},
    )
    assert missing_child.status_code == 422

    no_response = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={
            "answers": [
                {"question_id": parent["id"], "answer_text": "no"},
                {"question_id": child["id"], "option_id": child["options"][0]["id"]},
            ]
        },
    )
    assert no_response.status_code == 201, no_response.get_json()

    stats = client.get(
        f"/api/surveys/{survey['id']}/statistics", headers=headers
    ).get_json()["data"]
    assert stats["overview"]["average_score"] == 7.0
    # Tối đa = 10 (nhánh "Có" tự đạt 10, cao hơn trần nhánh "Không" + câu hỏi phụ = 4).
    assert stats["overview"]["max_possible_score"] == 10.0
    assert stats["overview"]["average_total_score"] == 7.0
    assert stats["overview"]["average_percentage"] == 70.0
    branch_row = stats["by_branch"][0]
    assert branch_row["max_possible_score"] == 10.0
    assert branch_row["average_total_score"] == 7.0
    assert branch_row["average_percentage"] == 70.0


def test_trigger_branch_or_option_score_always_locked_to_null(client, admin_user, auth_header):
    """Điểm của nhánh/phương án đang kích hoạt câu hỏi phụ luôn lấy từ câu hỏi phụ —
    mọi cách gửi điểm lên (tạo câu hỏi phụ, sửa câu cha, sửa phương án trực tiếp) đều
    phải bị hệ thống ép về null, không phụ thuộc client gửi gì."""
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers, title="Khảo sát khóa điểm nhánh có câu hỏi phụ")

    parent = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Hồ sơ có xử lý đúng hạn không?",
            "question_type": "yes_no",
            "is_required": True,
            "yes_score": 10,
            "no_score": 5,
        },
    ).get_json()["data"]
    assert parent["no_score"] == 5

    single_parent = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Anh/chị đánh giá thế nào?",
            "question_type": "single_choice",
            "is_required": True,
            "options": [
                {"option_text": "Tốt", "score": 10},
                {"option_text": "Không tốt", "score": 3},
            ],
        },
    ).get_json()["data"]
    bad_option_id = single_parent["options"][1]["id"]

    # Liên kết câu hỏi phụ vào nhánh "no" của parent và vào phương án "Không tốt".
    child_yes_no = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Nếu không, nguyên nhân là gì?",
            "question_type": "single_choice",
            "is_required": True,
            "parent_question_id": parent["id"],
            "trigger_answer": "no",
            "options": [{"option_text": "Lý do A", "score": 2}, {"option_text": "Lý do B", "score": 1}],
        },
    ).get_json()["data"]
    client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Vì sao không tốt?",
            "question_type": "single_choice",
            "is_required": True,
            "parent_question_id": single_parent["id"],
            "trigger_option_id": bad_option_id,
            "options": [{"option_text": "Lý do C", "score": 2}, {"option_text": "Lý do D", "score": 1}],
        },
    ).get_json()["data"]

    # Sửa câu cha yes/no và cố gửi lại no_score=99 — vẫn phải bị ép về null vì nhánh "no" đã có câu hỏi phụ.
    updated_parent = client.put(
        f"/api/survey-questions/{parent['id']}",
        headers=headers,
        json={"no_score": 99},
    ).get_json()["data"]
    assert updated_parent["no_score"] is None
    assert updated_parent["yes_score"] == 10  # nhánh "yes" không có câu hỏi phụ, giữ nguyên được

    # Cố sửa trực tiếp phương án "Không tốt" — vẫn bị ép về null vì đang kích hoạt câu hỏi phụ.
    updated_option = client.put(
        f"/api/survey-options/{bad_option_id}",
        headers=headers,
        json={"score": 77},
    ).get_json()["data"]
    assert updated_option["score"] is None


def test_multiple_choice_deduction_scores_none_one_two_and_threshold(
    client, admin_user, auth_header
):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers, title="Khảo sát trừ điểm")
    response = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Chọn các lỗi được ghi nhận",
            "question_type": "multiple_choice",
            "scoring_mode": "deduction",
            "max_score": 10,
            "zero_score_at": 3,
            "options": [
                {"option_text": "Lỗi 1", "score": 3},
                {"option_text": "Lỗi 2", "score": 3},
                {"option_text": "Lỗi 3", "score": 3},
                {"option_text": "Lỗi 4", "score": 3},
            ],
        },
    )
    assert response.status_code == 201, response.get_json()
    question = response.get_json()["data"]
    option_ids = [option["id"] for option in question["options"]]
    client.post(
        f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"}
    )

    public = client.get(f"/api/public/surveys/{survey['slug']}").get_json()["data"]
    public_question = public["questions"][0]
    assert public_question["scoring_mode"] == "deduction"
    assert "max_score" not in public_question
    assert all("score" not in option for option in public_question["options"])

    for selected in ([], option_ids[:1], option_ids[:2], option_ids[:3]):
        result = client.post(
            f"/api/public/surveys/{survey['id']}/submit",
            json={"answers": [{"question_id": question["id"], "option_ids": selected}]},
        )
        assert result.status_code == 201, result.get_json()

    stats = client.get(
        f"/api/surveys/{survey['id']}/statistics", headers=headers
    ).get_json()["data"]
    assert stats["overview"]["average_score"] == 5.25
    assert stats["overview"]["score_answer_count"] == 4
    # Tối đa = 10 (max_score câu trừ điểm, đạt được khi không chọn phương án nào).
    assert stats["overview"]["max_possible_score"] == 10.0
    assert stats["overview"]["average_total_score"] == 5.25
    assert stats["overview"]["average_percentage"] == 52.5
    question_stats = stats["by_question"][0]["stats"]
    assert question_stats["average_score"] == 5.25
    assert question_stats["scored_answers"] == 4
    assert question_stats["scoring_mode"] == "deduction"


def test_scored_options_calculate_average_and_rank_branches(
    client, admin_user, auth_header, make_unit
):
    headers = auth_header("admin_test")
    branch_low = make_unit("SCORE-LOW", name="Chi nhánh điểm thấp", unit_type="BRANCH")
    branch_high = make_unit("SCORE-HIGH", name="Chi nhánh điểm cao", unit_type="BRANCH")
    survey = _create_survey(client, headers, title="Khảo sát có chấm điểm")
    question = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Mức độ hài lòng?",
            "question_type": "single_choice",
            "is_required": True,
            "options": [
                {"option_text": "Chưa tốt", "score": -10},
                {"option_text": "Rất tốt", "score": 100},
            ],
        },
    ).get_json()["data"]
    assert [option["score"] for option in question["options"]] == [-10.0, 100.0]

    client.post(
        f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"}
    )
    public = client.get(f"/api/public/surveys/{survey['slug']}").get_json()["data"]
    assert all("score" not in option for option in public["questions"][0]["options"])

    low_option, high_option = question["options"]
    for branch, option in ((branch_low, low_option), (branch_high, high_option)):
        response = client.post(
            f"/api/public/surveys/{survey['id']}/submit",
            json={
                "branch_id": branch.id,
                "answers": [{"question_id": question["id"], "option_id": option["id"]}],
            },
        )
        assert response.status_code == 201, response.get_json()

    stats = client.get(
        f"/api/surveys/{survey['id']}/statistics", headers=headers
    ).get_json()["data"]
    assert stats["overview"]["average_score"] == 45.0
    assert stats["overview"]["score_answer_count"] == 2
    assert stats["by_branch"][0]["branch_id"] == branch_high.id
    assert stats["by_branch"][0]["rank"] == 1
    assert stats["by_branch"][0]["average_score"] == 100.0
    assert stats["by_branch"][1]["rank"] == 2
    question_stats = stats["by_question"][0]["stats"]
    assert question_stats["average_score"] == 45.0

    # Đổi điểm sau khi đã có phản hồi phải tạo phiên bản phương án mới; điểm
    # của phản hồi lịch sử vẫn giữ nguyên là 5.
    revised = client.put(
        f"/api/survey-options/{high_option['id']}",
        headers=headers,
        json={"score": 500},
    ).get_json()["data"]
    assert revised["revised_from_id"] == high_option["id"]
    assert revised["score"] == 500.0
    stats_after = client.get(
        f"/api/surveys/{survey['id']}/statistics", headers=headers
    ).get_json()["data"]
    assert stats_after["overview"]["average_score"] == 45.0


def test_sections_yes_no_scores_and_question_copy(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    survey = _create_survey(client, headers, title="Khảo sát theo phần")
    section = client.post(
        f"/api/surveys/{survey['id']}/sections",
        headers=headers,
        json={"title": "Phần 1. Tiếp nhận"},
    )
    assert section.status_code == 201, section.get_json()
    section = section.get_json()["data"]

    question = client.post(
        f"/api/surveys/{survey['id']}/questions",
        headers=headers,
        json={
            "question_text": "Hồ sơ có được hướng dẫn đầy đủ không?",
            "question_type": "yes_no",
            "section_id": section["id"],
            "yes_score": 25.5,
            "no_score": -7,
        },
    )
    assert question.status_code == 201, question.get_json()
    question = question.get_json()["data"]
    assert question["section_id"] == section["id"]
    assert question["yes_score"] == 25.5
    assert question["no_score"] == -7.0

    copied = client.post(
        f"/api/survey-questions/{question['id']}/duplicate", headers=headers
    ).get_json()["data"]
    assert copied["section_id"] == section["id"]
    assert copied["yes_score"] == 25.5
    assert copied["no_score"] == -7.0

    renamed = client.put(
        f"/api/survey-sections/{section['id']}",
        headers=headers,
        json={"title": "Phần 1. Hướng dẫn"},
    )
    assert renamed.status_code == 200
    questions = client.get(
        f"/api/surveys/{survey['id']}/questions", headers=headers
    ).get_json()["data"]
    assert all(item["section"] == "Phần 1. Hướng dẫn" for item in questions)
    assert client.delete(
        f"/api/survey-sections/{section['id']}", headers=headers
    ).status_code == 409

    client.post(
        f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"}
    )
    public = client.get(f"/api/public/surveys/{survey['slug']}").get_json()["data"]
    public_question = next(item for item in public["questions"] if item["id"] == question["id"])
    assert "yes_score" not in public_question
    response = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": question["id"], "answer_text": "yes"}]},
    )
    assert response.status_code == 201, response.get_json()
    stats = client.get(
        f"/api/surveys/{survey['id']}/statistics", headers=headers
    ).get_json()["data"]
    assert stats["overview"]["average_score"] == 25.5
    question_stats = next(
        item["stats"] for item in stats["by_question"] if item["id"] == question["id"]
    )
    assert question_stats["average_score"] == 25.5
    assert question_stats["yes_score"] == 25.5

    revised = client.put(
        f"/api/survey-questions/{question['id']}",
        headers=headers,
        json={"yes_score": 999, "no_score": -999},
    ).get_json()["data"]
    assert revised["revised_from_id"] == question["id"]
    stats_after = client.get(
        f"/api/surveys/{survey['id']}/statistics", headers=headers
    ).get_json()["data"]
    assert stats_after["overview"]["average_score"] == 25.5


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


def test_non_anonymous_survey_requires_name_phone_and_id_number(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    created = client.post(
        "/api/surveys",
        headers=headers,
        json={"title": "Khảo sát định danh", "is_anonymous": False},
    )
    survey = created.get_json()["data"]
    assert survey["is_anonymous"] is False
    q = _add_choice_question(client, headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})

    opt_id = q["options"][0]["id"]
    missing = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"answers": [{"question_id": q["id"], "option_id": opt_id}]},
    )
    assert missing.status_code == 422

    missing_id_number = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={
            "respondent_name": "Trần Thị B",
            "respondent_phone": "0909000111",
            "answers": [{"question_id": q["id"], "option_id": opt_id}],
        },
    )
    assert missing_id_number.status_code == 422

    ok_cmnd = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={
            "respondent_name": "Trần Thị B",
            "respondent_phone": "0909000111",
            "respondent_id_number": "123456789",
            "answers": [{"question_id": q["id"], "option_id": opt_id}],
        },
    )
    assert ok_cmnd.status_code == 201, ok_cmnd.get_json()

    ok_cccd = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={
            "respondent_name": "Trần Thị B",
            "respondent_phone": "0909000111",
            "respondent_id_number": "079123456789",
            "answers": [{"question_id": q["id"], "option_id": opt_id}],
        },
    )
    assert ok_cccd.status_code == 201, ok_cccd.get_json()


def test_branch_quota_locks_branch_once_full(client, admin_user, auth_header, make_unit):
    headers = auth_header("admin_test")
    branch = make_unit("QUOTA-BRANCH", name="CN Chỉ tiêu", unit_type="BRANCH")
    survey = _create_survey(client, headers)
    q = _add_choice_question(client, headers, survey["id"])
    client.post(f"/api/surveys/{survey['id']}/status", headers=headers, json={"status": "active"})

    limits = client.put(
        f"/api/surveys/{survey['id']}/branch-limits",
        headers=headers,
        json={"items": [{"branch_id": branch.id, "max_responses": 1}]},
    )
    assert limits.status_code == 200, limits.get_json()
    row = next(r for r in limits.get_json()["data"] if r["branch_id"] == branch.id)
    assert row["max_responses"] == 1

    opt_id = q["options"][0]["id"]
    first = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"branch_id": branch.id, "answers": [{"question_id": q["id"], "option_id": opt_id}]},
    )
    assert first.status_code == 201, first.get_json()

    public_after = client.get(f"/api/public/surveys/{survey['slug']}").get_json()["data"]
    assert next(b for b in public_after["branches"] if b["id"] == branch.id)["full"] is True

    second = client.post(
        f"/api/public/surveys/{survey['id']}/submit",
        json={"branch_id": branch.id, "answers": [{"question_id": q["id"], "option_id": opt_id}]},
    )
    assert second.status_code == 400, second.get_json()

    cleared = client.put(
        f"/api/surveys/{survey['id']}/branch-limits",
        headers=headers,
        json={"items": [{"branch_id": branch.id, "max_responses": None}]},
    )
    assert cleared.status_code == 200
    row = next(r for r in cleared.get_json()["data"] if r["branch_id"] == branch.id)
    assert row["max_responses"] is None


def test_duplicate_survey_copies_branch_limits(client, admin_user, auth_header, make_unit):
    headers = auth_header("admin_test")
    branch = make_unit("DUP-BRANCH", name="CN Sao chép", unit_type="BRANCH")
    survey = _create_survey(client, headers, title="Khảo sát gốc")
    _add_choice_question(client, headers, survey["id"])
    client.put(
        f"/api/surveys/{survey['id']}/branch-limits",
        headers=headers,
        json={"items": [{"branch_id": branch.id, "max_responses": 200}]},
    )

    dup = client.post(f"/api/surveys/{survey['id']}/duplicate", headers=headers)
    assert dup.status_code == 201, dup.get_json()
    new_survey = dup.get_json()["data"]
    assert new_survey["id"] != survey["id"]

    dup_limits = client.get(
        f"/api/surveys/{new_survey['id']}/branch-limits", headers=headers
    ).get_json()["data"]
    row = next(r for r in dup_limits if r["branch_id"] == branch.id)
    assert row["max_responses"] == 200

    # Sửa chỉ tiêu ở bản gốc không ảnh hưởng bản sao (hai bản ghi độc lập).
    client.put(
        f"/api/surveys/{survey['id']}/branch-limits",
        headers=headers,
        json={"items": [{"branch_id": branch.id, "max_responses": 50}]},
    )
    dup_limits_after = client.get(
        f"/api/surveys/{new_survey['id']}/branch-limits", headers=headers
    ).get_json()["data"]
    row_after = next(r for r in dup_limits_after if r["branch_id"] == branch.id)
    assert row_after["max_responses"] == 200
