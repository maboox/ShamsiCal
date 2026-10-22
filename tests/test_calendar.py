from datetime import date

import jdatetime
import pytest

from shamsical import calendar as cal


@pytest.mark.parametrize(
    "gregorian,jalali",
    [
        (date(2024, 3, 20), (1403, 1, 1)),
        (date(2025, 3, 21), (1404, 1, 1)),
        (date(2026, 10, 21), (1405, 7, 29)),
    ],
)
def test_known_dates(gregorian, jalali):
    day = jdatetime.date(*jalali)
    assert day.togregorian() == gregorian
    assert jdatetime.date.fromgregorian(date=gregorian) == day


def test_leap_boundary_and_clamped_month_navigation():
    assert cal.month_length(1403, 12) == 30
    assert cal.month_length(1404, 12) == 29
    assert cal.shift_day(jdatetime.date(1403, 12, 30), 1) == jdatetime.date(1404, 1, 1)
    assert cal.shift_month(jdatetime.date(1404, 6, 31), 1) == jdatetime.date(1404, 7, 30)
    assert cal.shift_month(jdatetime.date(1404, 1, 31), -1) == jdatetime.date(1403, 12, 30)


def test_grid_matches_weekday_for_every_month():
    for year in (1200, 1399, 1400, 1403, 1404, 1405, 1600):
        for month in range(1, 13):
            day = jdatetime.date(year, month, 1)
            cells = cal.month_cells(day)
            for index, item in enumerate(cells):
                if item:
                    assert index % 7 == (item.togregorian().weekday() + 2) % 7
            assert len([cell for cell in cells if cell]) == cal.month_length(year, month)


def test_supported_boundaries_and_hijri_fallback():
    first, last = jdatetime.date(1200, 1, 1), jdatetime.date(1600, 12, 29)
    assert cal.shift_month(first, -1) == first
    assert cal.shift_day(first, -1) == first
    assert cal.shift_month(last, 1) == last
    assert "range" in cal.hijri_text(first, "en")
    assert cal.digits("1405/07/29", "fa") == "۱۴۰۵/۰۷/۲۹"
