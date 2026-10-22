"""Calendar calculations without GUI, network, or locale side effects."""

from datetime import date, timedelta

import jdatetime
from hijridate import Gregorian

MONTHS_FA = "فروردین اردیبهشت خرداد تیر مرداد شهریور مهر آبان آذر دی بهمن اسفند".split()
MONTHS_EN = "Farvardin Ordibehesht Khordad Tir Mordad Shahrivar Mehr Aban Azar Dey Bahman Esfand".split()
WEEKDAYS_FA = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
WEEKDAYS_EN = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
HIJRI_FA = [
    "محرم",
    "صفر",
    "ربیع‌الاول",
    "ربیع‌الثانی",
    "جمادی‌الاول",
    "جمادی‌الثانی",
    "رجب",
    "شعبان",
    "رمضان",
    "شوال",
    "ذی‌القعده",
    "ذی‌الحجه",
]
MIN_YEAR, MAX_YEAR = 1200, 1600


def digits(value, language="fa"):
    text = str(value)
    return text.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")) if language == "fa" else text


def today():
    return jdatetime.date.fromgregorian(date=date.today())


def month_length(year, month):
    if month <= 6:
        return 31
    if month <= 11:
        return 30
    return 30 if jdatetime.date(year, 1, 1).isleap() else 29


def shift_month(day, delta):
    index = day.year * 12 + day.month - 1 + delta
    year, month = divmod(index, 12)
    if not MIN_YEAR <= year <= MAX_YEAR:
        return day
    return jdatetime.date(year, month + 1, min(day.day, month_length(year, month + 1)))


def shift_day(day, delta):
    result = day + timedelta(days=delta)
    return result if MIN_YEAR <= result.year <= MAX_YEAR else day


def month_cells(day):
    first = day.replace(day=1)
    offset = (first.togregorian().weekday() + 2) % 7
    return [None] * offset + [first.replace(day=n) for n in range(1, month_length(day.year, day.month) + 1)]


def heading(day, language):
    names = MONTHS_FA if language == "fa" else MONTHS_EN
    return f"{names[day.month - 1]} {digits(day.year, language)}"


def hijri_text(day, language):
    try:
        value = Gregorian.fromdate(day.togregorian()).to_hijri()
    except (ValueError, OverflowError):
        return "خارج از بازهٔ تقویم قمری" if language == "fa" else "Outside Hijri calendar range"
    month = HIJRI_FA[value.month - 1] if language == "fa" else value.month_name("en")
    return digits(f"{value.day} {month} {value.year}", language)
