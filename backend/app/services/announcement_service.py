"""Nghiệp vụ bảng tin nội bộ: phạm vi người nhận, vòng đời và đã đọc."""
from __future__ import annotations

from sqlalchemy import and_, or_

from ..common.exceptions import BusinessRuleError, NotFoundError, PermissionDeniedError, ValidationError
from ..common.utils import clean_str, ensure_aware, parse_pagination, utcnow
from ..extensions import db
from ..models import Announcement, AnnouncementRead, OrganizationUnit, Role, User
from ..models.announcement import ANNOUNCEMENT_AUDIENCES
from ..permissions import constants as perms
from .audit_service import record_audit


def _get_or_404(announcement_id: int) -> Announcement:
    item = db.session.get(Announcement, announcement_id)
    if item is None:
        raise NotFoundError("Không tìm thấy thông báo.")
    return item


def _current_unit_id(user: User) -> int | None:
    assignment = user.employee.primary_active_assignment() if user.employee else None
    return assignment.unit_id if assignment else None


def _published_filter(user: User):
    now = utcnow()
    audience_filters = [Announcement.audience_type == "ALL"]
    unit_id = _current_unit_id(user)
    if unit_id:
        audience_filters.append(
            and_(
                Announcement.audience_type == "UNIT",
                Announcement.units.any(OrganizationUnit.id == unit_id),
            )
        )
    role_ids = [role.id for role in user.roles]
    if role_ids:
        audience_filters.append(
            and_(
                Announcement.audience_type == "ROLE",
                Announcement.roles.any(Role.id.in_(role_ids)),
            )
        )
    audience_filters.append(
        and_(
            Announcement.audience_type == "USER",
            Announcement.users.any(User.id == user.id),
        )
    )
    return and_(
        Announcement.status == "published",
        or_(Announcement.published_at.is_(None), Announcement.published_at <= now),
        or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
        or_(*audience_filters),
    )


def _can_edit(item: Announcement, actor: User) -> bool:
    return actor.has_permission(perms.ANNOUNCEMENT_MANAGE) or (
        item.created_by == actor.id and actor.has_permission(perms.ANNOUNCEMENT_CREATE)
    )


def _is_visible(item: Announcement, actor: User) -> bool:
    if actor.has_permission(perms.ANNOUNCEMENT_MANAGE) or _can_edit(item, actor):
        return True
    if item.status != "published":
        return False
    now = utcnow()
    if item.published_at and ensure_aware(item.published_at) > now:
        return False
    if item.expires_at and ensure_aware(item.expires_at) <= now:
        return False
    if item.audience_type == "ALL":
        return True
    if item.audience_type == "UNIT":
        return _current_unit_id(actor) in {unit.id for unit in item.units}
    if item.audience_type == "ROLE":
        return bool({role.id for role in actor.roles} & {role.id for role in item.roles})
    if item.audience_type == "USER":
        return actor.id in {user.id for user in item.users}
    return False


def _set_audience(item: Announcement, audience_type: str, audience_ids: list[int]) -> None:
    audience_type = (audience_type or "ALL").upper()
    if audience_type not in ANNOUNCEMENT_AUDIENCES:
        raise ValidationError("Đối tượng nhận thông báo không hợp lệ.")
    ids = sorted({int(value) for value in (audience_ids or [])})
    item.audience_type = audience_type
    item.units = []
    item.roles = []
    item.users = []
    if audience_type == "ALL":
        return
    if not ids:
        raise ValidationError("Vui lòng chọn ít nhất một đối tượng nhận thông báo.")
    model = {"UNIT": OrganizationUnit, "ROLE": Role, "USER": User}[audience_type]
    rows = db.session.query(model).filter(model.id.in_(ids)).all()
    if len(rows) != len(ids):
        raise ValidationError("Có đối tượng nhận không tồn tại hoặc đã bị xóa.")
    if audience_type == "UNIT":
        item.units = rows
    elif audience_type == "ROLE":
        item.roles = rows
    else:
        item.users = rows


def list_announcements(args, *, actor: User) -> dict:
    page, page_size = parse_pagination(args, default_size=10, max_size=50)
    include_all = str(args.get("include_all", "")).lower() in {"1", "true"}
    query = db.session.query(Announcement)
    if include_all and (
        actor.has_permission(perms.ANNOUNCEMENT_MANAGE)
        or actor.has_permission(perms.ANNOUNCEMENT_PUBLISH)
    ):
        pass
    elif include_all and actor.has_permission(perms.ANNOUNCEMENT_CREATE):
        query = query.filter(or_(_published_filter(actor), Announcement.created_by == actor.id))
    else:
        query = query.filter(_published_filter(actor))

    keyword = clean_str(args.get("keyword") or args.get("q"))
    if keyword:
        term = f"%{keyword}%"
        query = query.filter(or_(Announcement.title.ilike(term), Announcement.content.ilike(term)))
    category = clean_str(args.get("category"))
    if category:
        query = query.filter(Announcement.category == category)
    status = clean_str(args.get("status"))
    if status and include_all:
        query = query.filter(Announcement.status == status)

    total = query.count()
    rows = (
        query.order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc(), Announcement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    read_ids = {
        row.announcement_id
        for row in db.session.query(AnnouncementRead.announcement_id).filter(
            AnnouncementRead.user_id == actor.id,
            AnnouncementRead.announcement_id.in_([item.id for item in rows] or [-1]),
        )
    }
    return {
        "items": [item.to_dict(is_read=item.id in read_ids) for item in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "unread": sum(1 for item in rows if item.status == "published" and item.id not in read_ids),
    }


def get_announcement(announcement_id: int, *, actor: User) -> dict:
    item = _get_or_404(announcement_id)
    if not _is_visible(item, actor):
        raise PermissionDeniedError("Bạn không thuộc đối tượng nhận thông báo này.")
    is_read = (
        db.session.query(AnnouncementRead.id)
        .filter_by(announcement_id=item.id, user_id=actor.id)
        .first()
        is not None
    )
    return item.to_dict(is_read=is_read)


def create_announcement(data: dict, *, actor: User, meta: dict) -> dict:
    title = clean_str(data.get("title"))
    content = clean_str(data.get("content"))
    if not title or not content:
        raise ValidationError("Tiêu đề và nội dung thông báo là bắt buộc.")
    item = Announcement(
        title=title,
        content=content,
        category=clean_str(data.get("category")) or "Thông báo",
        is_pinned=bool(data.get("is_pinned", False)),
        expires_at=data.get("expires_at"),
        created_by=actor.id,
        updated_by=actor.id,
        status="draft",
    )
    _set_audience(item, data.get("audience_type", "ALL"), data.get("audience_ids", []))
    db.session.add(item)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="announcement.create",
        entity_type="announcement",
        entity_id=item.id,
        new_values=item.to_dict(),
        **meta,
    )
    db.session.commit()
    return item.to_dict()


def update_announcement(announcement_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    item = _get_or_404(announcement_id)
    if not _can_edit(item, actor):
        raise PermissionDeniedError("Bạn không có quyền sửa thông báo này.")
    if item.status != "draft" and not actor.has_permission(perms.ANNOUNCEMENT_MANAGE):
        raise BusinessRuleError(
            "Thông báo đã phát hành hoặc thu hồi; chỉ người quản lý có thể chỉnh sửa."
        )
    old = item.to_dict()
    if "title" in data:
        item.title = clean_str(data["title"]) or ""
    if "content" in data:
        item.content = clean_str(data["content"]) or ""
    if not item.title or not item.content:
        raise ValidationError("Tiêu đề và nội dung thông báo là bắt buộc.")
    if "category" in data:
        item.category = clean_str(data["category"]) or "Thông báo"
    if "is_pinned" in data:
        item.is_pinned = bool(data["is_pinned"])
    if "expires_at" in data:
        item.expires_at = data["expires_at"]
    if "audience_type" in data or "audience_ids" in data:
        next_audience_type = data.get("audience_type", item.audience_type)
        previous_ids = [target["id"] for target in old["audience_items"]]
        fallback_ids = previous_ids if next_audience_type == item.audience_type else []
        _set_audience(
            item,
            next_audience_type,
            data.get("audience_ids", fallback_ids),
        )
    item.updated_by = actor.id
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="announcement.update",
        entity_type="announcement",
        entity_id=item.id,
        old_values=old,
        new_values=item.to_dict(),
        **meta,
    )
    db.session.commit()
    return item.to_dict()


def set_status(announcement_id: int, status: str, *, actor: User, meta: dict) -> dict:
    item = _get_or_404(announcement_id)
    if status not in {"published", "archived"}:
        raise ValidationError("Trạng thái thông báo không hợp lệ.")
    old = item.to_dict()
    item.status = status
    item.updated_by = actor.id
    if status == "published":
        item.published_at = utcnow()
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action=f"announcement.{status}",
        entity_type="announcement",
        entity_id=item.id,
        old_values=old,
        new_values=item.to_dict(),
        **meta,
    )
    db.session.commit()
    return item.to_dict()


def delete_announcement(announcement_id: int, *, actor: User, meta: dict) -> None:
    item = _get_or_404(announcement_id)
    if not _can_edit(item, actor):
        raise PermissionDeniedError("Bạn không có quyền xóa thông báo này.")
    if item.status == "published" and not actor.has_permission(perms.ANNOUNCEMENT_MANAGE):
        raise BusinessRuleError("Thông báo đang phát hành; hãy thu hồi trước khi xóa.")
    old = item.to_dict()
    db.session.delete(item)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="announcement.delete",
        entity_type="announcement",
        entity_id=announcement_id,
        old_values=old,
        **meta,
    )
    db.session.commit()


def mark_read(announcement_id: int, *, actor: User) -> dict:
    item = _get_or_404(announcement_id)
    if not _is_visible(item, actor):
        raise PermissionDeniedError("Bạn không thuộc đối tượng nhận thông báo này.")
    row = db.session.query(AnnouncementRead).filter_by(
        announcement_id=item.id, user_id=actor.id
    ).first()
    if row is None:
        row = AnnouncementRead(announcement_id=item.id, user_id=actor.id)
        db.session.add(row)
        db.session.commit()
    return {"announcement_id": item.id, "is_read": True, "read_at": row.read_at.isoformat()}


def audience_options() -> dict:
    units = (
        db.session.query(OrganizationUnit)
        .filter(OrganizationUnit.is_active.is_(True))
        .order_by(OrganizationUnit.sort_index, OrganizationUnit.name)
        .all()
    )
    roles = db.session.query(Role).order_by(Role.name).all()
    users = db.session.query(User).filter(User.is_active.is_(True)).order_by(User.full_name).all()
    return {
        "units": [{"id": row.id, "name": row.display_path} for row in units],
        "roles": [{"id": row.id, "name": row.name} for row in roles],
        "users": [{"id": row.id, "name": row.full_name, "username": row.username} for row in users],
    }
