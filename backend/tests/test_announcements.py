"""Kiểm thử bảng tin nội bộ và giới hạn đối tượng nhận."""
from app.models import Role
from app.permissions.constants import ROLE_OFFICE_LEADER, ROLE_STAFF


def _create_and_publish(client, headers, **overrides):
    payload = {
        "title": "Thông báo lịch họp",
        "content": "Họp giao ban vào 08:00 sáng thứ Hai.",
        "category": "Lịch công tác",
        "audience_type": "ALL",
        "audience_ids": [],
        **overrides,
    }
    created = client.post("/api/announcements", json=payload, headers=headers)
    assert created.status_code == 201, created.get_json()
    item = created.get_json()["data"]
    published = client.post(
        f"/api/announcements/{item['id']}/status",
        json={"status": "published"},
        headers=headers,
    )
    assert published.status_code == 200, published.get_json()
    return item["id"]


def test_published_announcement_is_visible_and_can_be_marked_read(
    client, make_user, auth_header
):
    make_user("leader_news", role_code=ROLE_OFFICE_LEADER)
    make_user("staff_news", role_code=ROLE_STAFF)
    leader_headers = auth_header("leader_news")
    announcement_id = _create_and_publish(client, leader_headers)

    staff_headers = auth_header("staff_news")
    listed = client.get("/api/announcements", headers=staff_headers)
    assert listed.status_code == 200
    assert listed.get_json()["data"]["items"][0]["id"] == announcement_id
    assert listed.get_json()["data"]["items"][0]["is_read"] is False

    marked = client.post(
        f"/api/announcements/{announcement_id}/read", headers=staff_headers
    )
    assert marked.status_code == 200

    listed_again = client.get("/api/announcements", headers=staff_headers)
    assert listed_again.get_json()["data"]["items"][0]["is_read"] is True


def test_user_targeted_announcement_is_hidden_from_other_users(
    client, make_user, auth_header
):
    make_user("leader_target", role_code=ROLE_OFFICE_LEADER)
    recipient = make_user("recipient_target", role_code=ROLE_STAFF)
    make_user("other_target", role_code=ROLE_STAFF)
    leader_headers = auth_header("leader_target")
    announcement_id = _create_and_publish(
        client,
        leader_headers,
        title="Thông báo cá nhân",
        audience_type="USER",
        audience_ids=[recipient.id],
    )

    recipient_list = client.get(
        "/api/announcements", headers=auth_header("recipient_target")
    )
    assert [row["id"] for row in recipient_list.get_json()["data"]["items"]] == [
        announcement_id
    ]

    other_list = client.get("/api/announcements", headers=auth_header("other_target"))
    assert other_list.get_json()["data"]["items"] == []


def test_staff_cannot_create_or_publish(client, make_user, auth_header):
    make_user("staff_denied", role_code=ROLE_STAFF)
    headers = auth_header("staff_denied")
    response = client.post(
        "/api/announcements",
        json={"title": "Không được phép", "content": "Nội dung"},
        headers=headers,
    )
    assert response.status_code == 403


def test_permissions_are_available_for_role_configuration(app, db):
    system_admin = db.session.query(Role).filter_by(code="SYSTEM_ADMIN").one()
    assert {
        "announcement.view",
        "announcement.create",
        "announcement.publish",
        "announcement.manage",
    }.issubset(system_admin.permission_codes())
