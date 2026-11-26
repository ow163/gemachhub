"""בדיקות מערכת (System / Integration) ל-GemachHub, דרך הדפדפן מול המערכת הרצה.

כל בדיקה מתאימה ל-Test Case ב-Azure DevOps (TC-01 עד TC-10) ומקושרת לסיפורי המשתמש שהיא בודקת.
"""
import re
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from conftest import PHOTO, SATURDAY, free_weekday, is_rest_day, unique_phone


def test_tc01_catalog_by_category_loads_fast(page):
    """TC-01 (AB#88): הקטלוג נטען תוך 2 שניות, ליד כל קטגוריה מספר הפריטים, וסינון לפי קטגוריה עובד."""
    page.goto("/")
    expect(page.locator("#catalog-items .item").first).to_be_visible()
    ms = int(page.locator("#catalog-timing").get_attribute("data-ms"))
    assert ms < 2000, f"הקטלוג נטען ב-{ms}ms"
    option = page.locator("#catalog-category option", has_text="תינוקות")
    expect(option).to_have_text(re.compile(r"תינוקות \(\d+\)"))
    page.select_option("#catalog-category", label=option.inner_text())
    expect(page.locator("#catalog-items .item .tag").first).to_have_text("תינוקות")
    tags = page.locator("#catalog-items .item .tag").all_inner_texts()
    assert tags and set(tags) == {"תינוקות"}
    card = page.locator("#catalog-items .item").first
    expect(card).to_contain_text("פיקדון: ₪")


def test_tc02_search_ignores_niqqud_and_suggests_assistant(page):
    """TC-02 (AB#93): חיפוש עם ניקוד ורווחים מוצא את הפריט, וכשאין תוצאות מוצע העוזר החכם."""
    page.goto("/")
    expect(page.locator("#catalog-items .item").first).to_be_visible()
    page.fill("#catalog-search", "  מֵיחַם  ")
    expect(page.locator("#catalog-items .item")).to_have_count(1)
    expect(page.locator("#catalog-items .item h3")).to_have_text("מיחם 100 כוסות")
    page.fill("#catalog-search", "טרקטור")
    expect(page.locator("#catalog-items .empty")).to_contain_text("העוזר החכם")


def test_tc03_points_map_shows_details_and_navigation(page):
    """TC-03 (AB#55): המפה מציגה רק נקודות פעילות, ולחיצה על נקודה מציגה כתובת, שעות וקישור ניווט."""
    page.goto("/")
    pins = page.locator("#points-map .pin")
    expect(pins).to_have_count(4)
    pins.first.click()
    details = page.locator("#point-details")
    expect(details).to_contain_text("רחוב ברזיל 14")
    expect(details).to_contain_text("שעות פעילות")
    link = details.locator("a", has_text="Google Maps")
    assert "google.com/maps/dir" in link.get_attribute("href")


def test_tc04_item_card_gallery_deposit_and_availability(page):
    """TC-04 (AB#103): כרטיס פריט מציג גלריה, פיקדון, תקופת השאלה מקסימלית וזמינות לפי נקודות."""
    page.goto("/")
    page.locator("#catalog-items .item-link", has_text="מיחם 100 כוסות").click()
    expect(page).to_have_url(re.compile(r"/item\.html\?id=3$"))
    expect(page.locator("#deposit")).to_have_text("פיקדון: ₪150")
    expect(page.locator("#max-days")).to_contain_text("7 ימים")
    expect(page.locator(".thumbs button")).to_have_count(2)
    page.locator(".thumbs button").nth(1).click()
    assert page.locator("#main-img").get_attribute("src").endswith("gemach-label.svg")
    expect(page.locator("#availability tbody tr")).to_have_count(2)


def test_tc05_donation_with_photo_and_status_tracking(page, api, tmp_path):
    """TC-05 (AB#258, AB#273): תרומה בלי תמונה נחסמת; עם תמונה מתקבל מספר פנייה; התורם רואה את הסטטוס ומקבל הודעה."""
    phone = unique_phone()
    page.goto("/")
    form = page.locator("#donate-form")
    form.locator("[name=donor_name]").fill("בודק מערכת")
    form.locator("[name=phone]").fill(phone)
    form.locator("[name=item_name]").fill("עגלת תאומים")
    form.locator("[name=point_id]").select_option(index=1)
    form.locator("button[type=submit]").click()
    expect(page.locator("#donate-msg")).to_contain_text("תמונה")

    img = tmp_path / "item.png"
    import base64
    img.write_bytes(base64.b64decode(PHOTO.split(",", 1)[1]))
    form.locator("[name=photo_file]").set_input_files(str(img))
    form.locator("button[type=submit]").click()
    expect(page.locator("#donate-msg")).to_contain_text("מספר הפנייה")
    ref = re.search(r"#(\d+)", page.locator("#donate-msg").inner_text()).group(1)

    page.fill("#mine-form [name=phone]", phone)
    page.locator("#mine-form button").click()
    expect(page.locator(f"#mine-list [data-donation-id='{ref}']")).to_contain_text("ממתינה לאישור")
    notes = api.get(f"/api/notifications?phone={phone}").json()
    assert any(f"פנייה מס' {ref}" in n["message"] for n in notes)


def test_tc06_point_inventory_and_overdue_list(page):
    """TC-06 (AB#236, AB#215): מלאי הנקודה לפי סטטוס עם סינון לפי פריט, ורשימת האיחורים ממוינת לפי ימי איחור."""
    page.goto("/inventory.html")
    expect(page.locator("#inv-summary .chip")).to_have_count(4)
    expect(page.locator("#inv-table tbody tr").first).not_to_contain_text("טוען")
    page.select_option("#inv-item", label="שולחן מתקפל 1.8 מ'")
    expect(page.locator("#inv-table tbody tr")).to_have_count(3)
    for row in page.locator("#inv-table tbody tr td:nth-child(2)").all_inner_texts():
        assert row == "שולחן מתקפל 1.8 מ'"

    page.goto("/overdue.html")
    row = page.locator("#od-table tbody tr[data-code='GH-1001']")
    expect(row).to_contain_text("0501111111")
    days = [int(x) for x in page.locator("#od-table .days-late").all_inner_texts()]
    assert days == sorted(days, reverse=True) and days[0] >= 1


def test_tc07_cart_limits_quantity_and_availability_by_dates(page):
    """TC-07 (AB#109, AB#98): אי אפשר לבחור כמות גדולה מהזמין, סה"כ הפיקדון מחושב, והקטלוג מסנן זמינות לפי תאריכים."""
    phone = unique_phone()
    page.goto("/cart.html")
    page.fill("#login-form [name=phone]", phone)
    page.locator("#login-form button").click()
    expect(page.locator("#login-state")).to_contain_text(phone)
    page.goto("/")
    page.locator(".item[data-item-id='7'] [data-add]").click()  # מגבר: יחידה אחת בכל הרשת
    expect(page.locator(".item[data-item-id='7'] [data-add]")).to_have_text("נוסף לעגלה ✓")
    page.goto("/cart.html")
    qty = page.locator("#cart-table tr[data-item-id='7'] .qty")
    expect(qty).to_have_value("1")
    expect(page.locator("#cart-total")).to_have_text("₪400")
    qty.fill("3")
    qty.dispatch_event("change")
    expect(page.locator("#cart-msg")).to_contain_text("אפשר להזמין עד 1")

    # זמינות בתאריכים: עגלת התינוק ברמות מושאלת עד עוד 4 ימים, ולכן היא לא זמינה בטווח ומוצג מתי תתפנה
    today = date.today().isoformat()
    page.goto("/")
    page.fill("#range-start", today)
    page.fill("#range-end", (date.today() + timedelta(days=1)).isoformat())
    page.select_option("#range-point", label='גמ"ח רמות')
    stroller = page.locator(".item[data-item-id='5']")
    expect(stroller).to_have_class(re.compile("unavailable"))
    expect(stroller).to_contain_text("יתפנה ב-")


def test_tc08_order_rules_and_my_loans(page):
    """TC-08 (AB#114, AB#151): איסוף בשבת נחסם; הזמנה תקינה מקבלת קוד ומופיעה בהשאלות שלי עם פרטי הנקודה."""
    phone = unique_phone()
    page.goto("/cart.html")
    page.fill("#login-form [name=phone]", phone)
    page.locator("#login-form button").click()
    expect(page.locator("#login-state")).to_contain_text(phone)
    page.request.put("/api/cart", data={"phone": phone, "item_id": 2, "qty": 1})
    page.reload()
    expect(page.locator("#order-card")).to_be_visible()

    form = page.locator("#order-form")
    form.locator("[name=name]").fill("בודק מערכת")
    form.locator("[name=point_id]").select_option(value="1")
    saturday = date.today() + timedelta(days=(SATURDAY - date.today().weekday()) % 7 or 7)
    form.locator("[name=start_date]").fill(saturday.isoformat())
    form.locator("[name=end_date]").fill((saturday + timedelta(days=1)).isoformat())
    form.locator("button[type=submit]").click()
    expect(page.locator("#order-msg")).to_contain_text("בשבת")

    start = free_weekday(14)
    form.locator("[name=start_date]").fill(start.isoformat())
    form.locator("[name=end_date]").fill((start + timedelta(days=1)).isoformat())
    form.locator("button[type=submit]").click()
    expect(page.locator("#order-confirm")).to_be_visible()
    code = page.locator("#order-confirm .code").inner_text()
    assert code.startswith("GH-")

    page.goto("/loans.html")
    loan = page.locator(f".loan[data-code='{code}']")
    expect(loan).to_contain_text("שוריינה")
    expect(loan).to_contain_text('גמ"ח קריית יובל')


def test_tc09_volunteer_pickup_handover_damage_and_return(page, api):
    """TC-09 (AB#173, AB#178, AB#204, AB#194): איסוף להיום, שגיאה בנקודה אחרת, מסירה, תיעוד נזק וקליטת החזרה."""
    today = date.today()
    if is_rest_day(today):
        pytest.skip("אין איסופים בשבת ובחג")
    end = today + timedelta(days=1)
    while is_rest_day(end):
        end += timedelta(days=1)
    phone = unique_phone()
    res = api.post("/api/orders", data={"name": "בודק מערכת", "phone": phone, "point_id": 1,
                                        "start_date": today.isoformat(), "end_date": end.isoformat(),
                                        "pickup_time": "17:00", "items": [{"item_id": 2, "qty": 1}]})
    assert res.status == 201, res.text()
    code = res.json()["code"]

    page.goto("/point.html")
    expect(page.locator(f"#pk-table tr[data-code='{code}']")).to_contain_text("ממתין")
    page.select_option("#pt-point", value="2")
    page.fill("#ho-form [name=query]", code)
    page.locator("#ho-form button[type=submit]").click()
    expect(page.locator("#ho-error")).to_contain_text("נקודה אחרת")

    page.select_option("#pt-point", value="1")
    page.fill("#ho-form [name=query]", code)
    page.locator("#ho-form button[type=submit]").click()
    box = page.locator(f".order-box[data-order='{code}']")
    expect(box.locator(".deposit-ok")).to_be_visible()
    box.locator("[data-handover]").click()
    expect(box).to_contain_text("נמסר!")
    expect(page.locator(f"#pk-table tr[data-code='{code}']")).to_contain_text("נאסף")

    page.fill("#rt-form [name=code]", code)
    page.locator("#rt-form button").click()
    unit = page.locator("#rt-order .units-list li").first
    unit_code = unit.get_attribute("data-code")
    unit.locator("[data-damage]").click()
    dialog = page.locator("#damage-dialog")
    dialog.locator("[name=severity]").select_option("light")
    dialog.locator("[name=description]").fill("שריטה במשענת")
    dialog.locator("button[type=submit]").click()
    expect(page.locator("#dm-msg")).to_contain_text("תמונה")  # בלי תמונה הנזק לא נשמר
    dialog.locator("#dm-cancel").click()

    page.fill("#scan-form [name=unit]", unit_code.lower())
    page.locator("#scan-form button").click()
    page.locator("#rt-submit").click()
    expect(page.locator("#rt-msg")).to_contain_text("מסגרת הפיקדון שוחררה")
    notes = api.get(f"/api/notifications?phone={phone}").json()
    assert any("שוחררה" in n["message"] for n in notes)


def test_tc10_admin_donation_decision_and_kpi(page, api):
    """TC-10 (AB#279, AB#300): דחייה בלי נימוק נחסמת, דחייה עם נימוק מודיעה לתורם, ולוח הבקרה נטען תוך 3 שניות עם סינון לפי נקודה."""
    phone = unique_phone()
    res = api.post("/api/donations", data={"donor_name": "תורם בדיקה", "phone": phone, "item_name": "פריט לבדיקה",
                                           "point_id": 1, "photo": PHOTO})
    assert res.status == 201, res.text()
    donation_id = res.json()["id"]

    page.goto("/admin.html")
    expect(page.locator("#kpi-cards .kpi")).to_have_count(8)
    ms = int(page.locator("#kpi-meta").get_attribute("data-ms"))
    assert ms < 3000, f"לוח הבקרה נטען ב-{ms}ms"
    page.select_option("#kpi-point", value="1")
    expect(page.locator("#kpi-meta")).to_contain_text("נתונים ליום")

    card = page.locator(f".donation[data-donation-id='{donation_id}']")
    card.locator("[data-decide=reject]").click()
    expect(card.locator(".msg")).to_contain_text("חובה לכתוב נימוק")
    card.locator("input").fill("יש לנו מספיק פריטים כאלה")
    card.locator("[data-decide=reject]").click()
    expect(card.locator(".msg")).to_contain_text("נדחתה")
    notes = api.get(f"/api/notifications?phone={phone}").json()
    assert any("נדחתה" in n["message"] and "מספיק" in n["message"] for n in notes)
