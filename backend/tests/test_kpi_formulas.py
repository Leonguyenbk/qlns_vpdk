"""Test thuần công thức KPI (mục 12-15 tài liệu dự thảo) — không cần CSDL."""
from __future__ import annotations

from datetime import datetime, timezone

from app.services.kpi_formulas import (
    apply_kn_cap,
    compute_ratio,
    merge_intervals,
    points_from_ratio,
    suggested_rating,
    total_excluded_days,
)


def _dt(y, m, d, h=0):
    return datetime(y, m, d, h, tzinfo=timezone.utc)


def test_zero_denominator_is_no_data_not_zero_or_hundred():
    r = compute_ratio(5, 0)
    assert r.no_data is True
    assert r.ratio_percent is None

    r2 = compute_ratio(5, None)
    assert r2.no_data is True
    assert r2.ratio_percent is None


def test_normal_ratio_computation():
    r = compute_ratio(8, 10)
    assert r.no_data is False
    assert r.ratio_percent == 80.0


def test_points_from_ratio_none_stays_none():
    assert points_from_ratio(None, 20) is None


def test_points_from_ratio_caps_at_max():
    # 150% hoàn thành vẫn không vượt trần điểm tối đa của tiêu chí
    assert points_from_ratio(150, 20) == 20.0
    assert points_from_ratio(50, 20) == 10.0


def test_apply_kn_cap_no_config_means_no_conversion_no_limit():
    converted, recognized = apply_kn_cap(10, None, None)
    assert converted == 10
    assert recognized == 10


def test_apply_kn_cap_applies_coefficient():
    converted, recognized = apply_kn_cap(10, 1.5, None)
    assert converted == 15.0
    assert recognized == 15.0


def test_apply_kn_cap_limits_cumulative_recognition():
    # Người đã được ghi nhận 18/20 CAP; nhiệm vụ mới quy đổi ra 5 -> chỉ còn nhận 2
    converted, recognized = apply_kn_cap(5, 1.0, cap_value=20, already_recognized=18)
    assert converted == 5.0
    assert recognized == 2.0
    # Khối lượng quy đổi thực tế (converted) KHÔNG bị xoá bởi CAP — vẫn lưu đủ 5
    assert converted != recognized


def test_apply_kn_cap_never_goes_negative_when_over_cap():
    converted, recognized = apply_kn_cap(5, 1.0, cap_value=20, already_recognized=25)
    assert converted == 5.0
    assert recognized == 0.0


def test_merge_overlapping_pause_intervals():
    intervals = [
        (_dt(2026, 1, 1), _dt(2026, 1, 5)),
        (_dt(2026, 1, 3), _dt(2026, 1, 8)),  # chồng lấn với khoảng trên
        (_dt(2026, 1, 10), _dt(2026, 1, 12)),  # tách biệt
    ]
    merged = merge_intervals(intervals)
    assert merged == [
        (_dt(2026, 1, 1), _dt(2026, 1, 8)),
        (_dt(2026, 1, 10), _dt(2026, 1, 12)),
    ]


def test_total_excluded_days_does_not_double_count_overlap():
    intervals = [
        (_dt(2026, 1, 1), _dt(2026, 1, 5)),   # 4 ngày
        (_dt(2026, 1, 3), _dt(2026, 1, 8)),   # chồng lấn 2 ngày với khoảng trên
    ]
    # Gộp lại đúng bằng 1/1 -> 8/1 = 7 ngày, KHÔNG phải 4 + 5 = 9 ngày (trừ trùng)
    assert total_excluded_days(intervals) == 7.0


def test_suggested_rating_is_only_a_hint_not_official():
    assert suggested_rating(None) is None
    assert suggested_rating(95) == "Hoàn thành xuất sắc nhiệm vụ"
    assert suggested_rating(75) == "Hoàn thành tốt nhiệm vụ"
    assert suggested_rating(55) == "Hoàn thành nhiệm vụ"
    assert suggested_rating(30) == "Không hoàn thành nhiệm vụ"
