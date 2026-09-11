"""Công thức tính KPI thuần (pure) theo tài liệu dự thảo — mục 12, 13, 14, 15.

Các hàm ở đây KHÔNG truy vấn CSDL — nhận số liệu đã tổng hợp, trả kết quả.
Việc xác định nhiệm vụ nào thuộc tử số/mẫu số (mục 12.2/14.2, còn nhiều điểm
"cần xác nhận") nằm ở ``kpi_service.py`` và được ghi lại rõ trong
``docs/TASK_KPI_ANALYSIS.md``.

QUY TẮC BẤT BIẾN — không được vi phạm ở bất kỳ chỗ gọi nào:
- Mẫu số 0 hoặc None -> tỷ lệ = None ("Chưa đủ dữ liệu/Chờ xác nhận"),
  KHÔNG BAO GIỜ tự quy về 0% hay 100%.
- Không áp dụng Kn/CAP minh hoạ mặc định: None nghĩa là chưa cấu hình.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RatioResult:
    numerator: float | None
    denominator: float | None
    ratio_percent: float | None  # None = "Chưa đủ dữ liệu/Chờ xác nhận"
    no_data: bool
    task_ids: list[int] = field(default_factory=list)


def compute_ratio(numerator: float | None, denominator: float | None, *, task_ids: list[int] | None = None) -> RatioResult:
    """Công thức chung cho Số lượng/Chất lượng/Tiến độ (mục 12.1/13.2/14.1).

    ratio% = numerator / denominator * 100 — mẫu số 0/None -> None.
    """
    if denominator is None or denominator == 0:
        return RatioResult(
            numerator=numerator, denominator=denominator, ratio_percent=None,
            no_data=True, task_ids=task_ids or [],
        )
    ratio = round(float(numerator or 0) / float(denominator) * 100, 2)
    return RatioResult(
        numerator=numerator, denominator=denominator, ratio_percent=ratio,
        no_data=False, task_ids=task_ids or [],
    )


def points_from_ratio(ratio_percent: float | None, max_points: float, *, cap_at_max: bool = True) -> float | None:
    """Quy đổi % (0-100) sang thang điểm — chuyển về hệ số 0-1 trước khi nhân
    điểm tối đa, có chặn trần theo tiêu chí (mục 12.3/13.2/14.1)."""
    if ratio_percent is None:
        return None
    fraction = ratio_percent / 100.0
    if cap_at_max:
        fraction = min(fraction, 1.0)
    fraction = max(fraction, 0.0)
    return round(fraction * float(max_points), 2)


def apply_kn_cap(
    actual_qty: float,
    kn_value: float | None,
    cap_value: float | None,
    *,
    already_recognized: float = 0.0,
) -> tuple[float, float]:
    """Quy đổi Kn rồi ghi nhận theo CAP luỹ kế (mục 11).

    - ``kn_value`` None -> không quy đổi (hệ số coi như 1.0, KHÔNG phải vì đó
      là mặc định chính thức mà vì chưa cấu hình).
    - ``cap_value`` None -> không giới hạn.
    - ``already_recognized`` là tổng đã ghi nhận trước đó CHO CÙNG sản phẩm,
      cùng người, cùng kỳ — để CAP áp theo luỹ kế, không theo từng nhiệm vụ
      đơn lẻ (một nhiệm vụ nhỏ không bị cắt oan nếu CAP còn dư).

    Trả về ``(converted, recognized)``. ``converted`` luôn được lưu riêng —
    CAP không bao giờ được ghi đè/xoá số liệu khối lượng thực tế.
    """
    kn = float(kn_value) if kn_value is not None else 1.0
    converted = float(actual_qty) * kn
    if cap_value is None:
        recognized = converted
    else:
        remaining = max(0.0, float(cap_value) - already_recognized)
        recognized = min(converted, remaining)
    return converted, recognized


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Gộp các khoảng tạm dừng/chờ chồng lấn trước khi trừ (mục 14.3) — tránh
    trừ thời gian trùng lặp khi có nhiều lý do tạm dừng đè lên nhau."""
    clean = [(s, e) for s, e in intervals if s is not None and e is not None and e > s]
    if not clean:
        return []
    ordered = sorted(clean, key=lambda x: x[0])
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def total_excluded_days(intervals: list[tuple[datetime, datetime]]) -> float:
    merged = merge_intervals(intervals)
    seconds = sum((end - start).total_seconds() for start, end in merged)
    return seconds / 86400.0


RATING_THRESHOLDS = (
    (90, "Hoàn thành xuất sắc nhiệm vụ"),
    (70, "Hoàn thành tốt nhiệm vụ"),
    (50, "Hoàn thành nhiệm vụ"),
)


def suggested_rating(total_points: float | None) -> str | None:
    """CHỈ LÀ GỢI Ý theo ngưỡng điểm mục 15.1 — tài liệu quy định ngưỡng điểm
    KHÔNG đương nhiên là mức xếp loại (còn điều kiện loại trừ mục 15.2, trần
    tỷ lệ mục 15.3). Không bao giờ dùng giá trị này làm ``official_rating``
    tự động — luôn cần người có thẩm quyền xác nhận."""
    if total_points is None:
        return None
    for threshold, label in RATING_THRESHOLDS:
        if total_points >= threshold:
            return label
    return "Không hoàn thành nhiệm vụ"
