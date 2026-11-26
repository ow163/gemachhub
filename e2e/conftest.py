"""הגדרות משותפות לבדיקות המערכת (Playwright).

כתובת האתר נקבעת במשתנה הסביבה BASE_URL (ברירת מחדל: http://localhost:5173).
הבדיקות מניחות שבסיס הנתונים נטען עם db/seed.sql, ויוצרות לעצמן את שאר הנתונים דרך ה-API.
"""
import os
import random
from datetime import date, timedelta

import pytest
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5173").rstrip("/")
PHOTO = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
SATURDAY = 5


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(base_url=BASE_URL, locale="he-IL", viewport={"width": 1200, "height": 900})
    pg = context.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    yield pg
    context.close()
    assert not errors, f"שגיאות JavaScript בדף: {errors}"


@pytest.fixture
def api(browser):
    context = browser.new_context(base_url=BASE_URL)
    yield context.request
    context.close()


def unique_phone():
    return "058" + str(random.randint(1000000, 9999999))


# החגים שבנתוני הדוגמה (db/seed.sql). הבדיקות נמנעות מהם כשהן בוחרות תאריך אקראי.
SEED_HOLIDAYS = {"2027-04-22", "2027-04-28", "2027-06-11", "2027-10-02", "2027-10-03", "2027-10-11", "2027-10-16", "2027-10-23"}


def is_rest_day(d):
    return d.weekday() == SATURDAY or d.isoformat() in SEED_HOLIDAYS


def free_weekday(start_offset, spread=600):
    """תאריך עתידי אקראי כך שגם הוא וגם היום שאחריו אינם שבת או חג.
    התאריך אקראי כדי שהרצות חוזרות של הבדיקות לא יתנגשו בהזמנות מהרצות קודמות."""
    d = date.today() + timedelta(days=start_offset + random.randint(0, spread))
    while is_rest_day(d) or is_rest_day(d + timedelta(days=1)):
        d += timedelta(days=1)
    return d
