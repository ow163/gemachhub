-- GemachHub - נתוני דוגמה (אפשר להריץ שוב, הסקריפט מנקה קודם)
truncate audit_log, order_units, orders, cart_items, holidays, notifications, donations, units, items, points, categories restart identity cascade;

insert into categories (name, sort_order) values
    ('ריהוט לאירועים', 1),
    ('מטבח והגשה', 2),
    ('תינוקות', 3),
    ('הגברה', 4),
    ('רפואי', 5);

insert into points (name, neighborhood, address, opening_hours, lat, lng, open_time, close_time) values
    ('גמ"ח קריית יובל', 'קריית יובל', 'רחוב ברזיל 14, ירושלים', 'א-ה 17:00-20:00', 31.7651, 35.1762, '17:00', '20:00'),
    ('גמ"ח גילה',       'גילה',       'רחוב הגננת 5, ירושלים', 'א,ג,ה 18:00-21:00', 31.7329, 35.1884, '18:00', '21:00'),
    ('גמ"ח רמות',       'רמות',       'שדרות גולדה מאיר 120, ירושלים', 'א-ה 16:00-19:00', 31.8148, 35.1953, '16:00', '19:00'),
    ('גמ"ח בית הכרם',   'בית הכרם',   'רחוב החלוץ 30, ירושלים', 'ב,ד 19:00-21:30', 31.7794, 35.1908, '19:00', '21:30');

insert into items (name, category_id, description, deposit_amount, max_loan_days) values
    ('שולחן מתקפל 1.8 מ''',  1, 'שולחן מתקפל לשמונה איש', 100, 7),
    ('כיסא פלסטיק לבן',      1, 'כיסא מתקפל, נמכר בחבילות של 10', 10, 7),
    ('מיחם 100 כוסות',        2, 'מיחם חשמלי לשבת ולאירועים', 150, 7),
    ('פלטה חשמלית גדולה',     2, 'פלטה לשבת, 60x40 ס"מ', 120, 7),
    ('עגלת תינוק',            3, 'עגלה עם סל שכיבה', 300, 30),
    ('לול מתקפל',             3, 'לול נייד לתינוק', 150, 30),
    ('מגבר ומיקרופון אלחוטי', 4, 'מערכת הגברה ניידת לאירוע עד 150 איש', 400, 3),
    ('כיסא גלגלים',           5, 'כיסא גלגלים סטנדרטי מתקפל', 500, 60),
    ('הליכון',                5, 'הליכון עם גלגלים', 200, 60);

-- יחידות בנקודות (חלקן מושאלות או בתיקון)
insert into units (item_id, point_id, code, status) values
    (1, 1, 'KY-TBL-01', 'available'), (1, 1, 'KY-TBL-02', 'available'), (1, 1, 'KY-TBL-03', 'loaned'),
    (1, 2, 'GL-TBL-01', 'available'),
    (2, 1, 'KY-CHR-01', 'available'), (2, 1, 'KY-CHR-02', 'available'), (2, 3, 'RM-CHR-01', 'available'),
    (3, 1, 'KY-URN-01', 'available'), (3, 1, 'KY-URN-02', 'repair'), (3, 4, 'BK-URN-01', 'available'),
    (4, 2, 'GL-PLT-01', 'available'),
    (5, 3, 'RM-STR-01', 'loaned'), (5, 4, 'BK-STR-01', 'available'),
    (6, 3, 'RM-PLY-01', 'available'),
    (7, 1, 'KY-AMP-01', 'available'),
    (8, 2, 'GL-WCH-01', 'available'), (8, 3, 'RM-WCH-01', 'loaned'),
    (9, 4, 'BK-WLK-01', 'available');

-- גלריית תמונות לכל פריט (AB#103)
update items set images = array['/img/cat-' || category_id || '.svg', '/img/gemach-label.svg'];

-- חגים לפי הלוח העברי, כפי שהם בישראל (AB#114)
insert into holidays (day, name) values
    ('2026-09-12', 'ראש השנה'), ('2026-09-13', 'ראש השנה'), ('2026-09-21', 'יום כיפור'),
    ('2026-09-26', 'סוכות'), ('2026-10-03', 'שמיני עצרת'),
    ('2027-04-22', 'פסח'), ('2027-04-28', 'שביעי של פסח'), ('2027-06-11', 'שבועות'),
    ('2027-10-02', 'ראש השנה'), ('2027-10-03', 'ראש השנה'), ('2027-10-11', 'יום כיפור'),
    ('2027-10-16', 'סוכות'), ('2027-10-23', 'שמיני עצרת');

-- הזמנות לדוגמה, בתאריכים יחסיים להיום (AB#151)
insert into orders (code, borrower_name, phone, point_id, start_date, end_date, pickup_time, status, deposit_total, picked_up_at, returned_at) values
    ('GH-1001', 'דוד מזרחי',  '0501111111', 1, current_date - 12, current_date - 5, '17:30', 'picked_up', 100, now() - interval '12 days', null),
    ('GH-1002', 'רחל אברהם',  '0502222222', 3, current_date - 3,  current_date + 4, '16:30', 'picked_up', 800, now() - interval '3 days', null),
    ('GH-1003', 'יוסי כהן',   '0503333333', 1, current_date,      current_date + 3, '18:00', 'reserved',  110, null, null),
    ('GH-1004', 'דוד מזרחי',  '0501111111', 2, current_date - 40, current_date - 35, '18:30', 'returned', 100, now() - interval '40 days', now() - interval '35 days');
insert into order_units (order_id, unit_id, returned_at) values
    (1, 3, null), (2, 12, null), (2, 17, null), (3, 1, null), (3, 5, null), (4, 4, now() - interval '35 days');

-- תרומות לדוגמה שממתינות להחלטה (AB#279)
insert into donations (donor_name, phone, item_name, category_id, description, point_id, photo) values
    ('שרה לוי',   '0527654321', 'לול מתקפל',      3, 'כמעט חדש, עם מזרון', 2, '/img/cat-3.svg'),
    ('אבי גולן',  '0548887777', 'מיחם 60 כוסות', 2, 'עובד, צריך ניקוי אבנית', 1, '/img/cat-2.svg');
