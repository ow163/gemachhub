"""כללים משותפים להזמנות ולזמינות (AB#114, AB#98).

יחידה "תפוסה" בטווח תאריכים אם היא משויכת להזמנה פעילה שהתאריכים שלה חופפים לטווח.
השאלה שכבר נמסרה ועבר מועד ההחזרה שלה תופסת את היחידה עד שהיא מוחזרת בפועל.
"""
import re
from datetime import date

PHONE_RE = re.compile(r"^05\d-?\d{7}$")
SATURDAY = 5  # date.weekday(): שני=0 ... שבת=5

# תנאי SQL: היחידה u תפוסה בטווח %(start)s עד %(end)s
UNIT_BUSY_SQL = """
    exists (
        select 1
        from order_units ou
        join orders o on o.id = ou.order_id
        where ou.unit_id = u.id
          and ou.returned_at is null
          and o.status in ('reserved', 'picked_up')
          and o.start_date <= %(end)s::date
          and (case when o.status = 'picked_up' and o.end_date < current_date then 'infinity'::date
                    else o.end_date end) >= %(start)s::date
    )
"""


def normalize_phone(phone):
    phone = str(phone or "").strip()
    return phone.replace("-", "") if PHONE_RE.match(phone) else None


def parse_date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def rest_day_reason(day, holidays):
    """מחזיר סיבה אם אי אפשר לאסוף או להחזיר ביום הזה (שבת או חג), אחרת None."""
    if day.weekday() == SATURDAY:
        return "שבת"
    return holidays.get(day.isoformat())
