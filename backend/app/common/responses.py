"""Chuẩn hóa cấu trúc phản hồi API."""
from __future__ import annotations

from typing import Any

from flask import jsonify


def success(
    data: Any = None,
    message: str = "Thao tác thành công",
    status_code: int = 200,
):
    body = {
        "success": True,
        "message": message,
        "data": data,
        "errors": None,
    }
    return jsonify(body), status_code


def error(
    message: str = "Đã xảy ra lỗi",
    status_code: int = 400,
    errors: Any = None,
    data: Any = None,
):
    body = {
        "success": False,
        "message": message,
        "data": data,
        "errors": errors,
    }
    return jsonify(body), status_code


def paginated(items: list, page: int, page_size: int, total: int, message: str = "Thao tác thành công"):
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return success(
        data={
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        },
        message=message,
    )
