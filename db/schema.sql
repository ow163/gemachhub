-- GemachHub - סכמת בסיס הנתונים
-- מריצים פעם אחת: ב-Supabase דרך SQL Editor, או אוטומטית בקונטיינר ה-db המקומי.

create table if not exists categories (
    id          serial primary key,
    name        text not null unique,
    sort_order  int  not null default 0
);

create table if not exists points (
    id            serial primary key,
    name          text not null,
    neighborhood  text not null,
    address       text not null,
    opening_hours text not null,
    is_active     boolean not null default true
);

create table if not exists items (
    id              serial primary key,
    name            text not null,
    category_id     int  not null references categories(id),
    description     text not null default '',
    deposit_amount  int  not null check (deposit_amount >= 0),
    max_loan_days   int  not null default 7 check (max_loan_days > 0)
);

-- יחידה = עותק פיזי של פריט בנקודה מסוימת
create table if not exists units (
    id        serial primary key,
    item_id   int  not null references items(id),
    point_id  int  not null references points(id),
    code      text not null unique,
    status    text not null default 'available'
              check (status in ('available', 'loaned', 'repair', 'lost'))
);

-- הצעות תרומה של ציוד
create table if not exists donations (
    id           serial primary key,
    donor_name   text not null,
    phone        text not null,
    item_name    text not null,
    category_id  int  references categories(id),
    description  text not null default '',
    point_id     int  not null references points(id),
    status       text not null default 'pending'
                 check (status in ('pending', 'approved', 'rejected', 'received')),
    created_at   timestamptz not null default now()
);

create index if not exists idx_items_category on items(category_id);
create index if not exists idx_units_item_status on units(item_id, status);

-- אבטחה: חוסמים גישה ישירה מה-API הציבורי של Supabase.
-- ה-backend מתחבר כבעלים של הטבלאות ולכן לא מושפע.
alter table categories enable row level security;
alter table points     enable row level security;
alter table items      enable row level security;
alter table units      enable row level security;
alter table donations  enable row level security;

-- ===== ספרינט 1 =====
-- מפת נקודות (AB#55): מיקום ושעות פעילות מובנות לכל נקודה
alter table points add column if not exists lat        double precision;
alter table points add column if not exists lng        double precision;
alter table points add column if not exists open_time  time not null default '17:00';
alter table points add column if not exists close_time time not null default '20:00';

-- כרטיס פריט (AB#103): גלריית תמונות לכל פריט
alter table items add column if not exists images text[] not null default '{}';

-- טופס תרומה (AB#258): תמונה של הפריט (חובה)
alter table donations add column if not exists photo text;

-- הודעות למשתמשים (AB#273): כל הודעה שהמערכת שולחת נרשמת כאן
create table if not exists notifications (
    id          serial primary key,
    phone       text not null,
    channel     text not null default 'whatsapp',
    message     text not null,
    created_at  timestamptz not null default now()
);
create index if not exists idx_notifications_phone on notifications(phone);
alter table notifications enable row level security;

-- ===== ספרינט 2 =====
-- חגים (AB#114): ימים שבהם אין איסוף והחזרה, בנוסף לשבת
create table if not exists holidays (
    day   date primary key,
    name  text not null
);

-- עגלת הזמנה (AB#109): נשמרת בשרת לפי מספר הטלפון
create table if not exists cart_items (
    phone       text not null,
    item_id     int  not null references items(id),
    qty         int  not null check (qty > 0),
    updated_at  timestamptz not null default now(),
    primary key (phone, item_id)
);

-- הזמנות והשאלות (AB#114, AB#151)
create table if not exists orders (
    id             serial primary key,
    code           text not null unique,
    borrower_name  text not null,
    phone          text not null,
    point_id       int  not null references points(id),
    start_date     date not null,
    end_date       date not null,
    pickup_time    time not null,
    status         text not null default 'reserved'
                   check (status in ('reserved', 'picked_up', 'returned', 'cancelled')),
    deposit_total  int  not null default 0,
    created_at     timestamptz not null default now(),
    picked_up_at   timestamptz,
    returned_at    timestamptz,
    check (end_date >= start_date)
);

-- היחידות הפיזיות ששויכו לכל הזמנה
create table if not exists order_units (
    order_id     int not null references orders(id) on delete cascade,
    unit_id      int not null references units(id),
    returned_at  timestamptz,
    primary key (order_id, unit_id)
);

create index if not exists idx_orders_phone on orders(phone);
create index if not exists idx_orders_point_dates on orders(point_id, start_date, end_date);
create index if not exists idx_order_units_unit on order_units(unit_id);

alter table holidays    enable row level security;
alter table cart_items  enable row level security;
alter table orders      enable row level security;
alter table order_units enable row level security;

-- ===== ספרינט 3 =====
-- מצב הפיקדון בכל הזמנה (AB#178): held = מסגרת תפוסה ותקפה, released = שוחררה, charged = חויב
alter table orders add column if not exists deposit_status text not null default 'held'
    check (deposit_status in ('held', 'released', 'charged'));

-- החלטת מנהל על תרומה (AB#279)
alter table donations add column if not exists decision_reason text;
alter table donations add column if not exists decided_at timestamptz;

-- יומן פעולות (AB#279): כל החלטה של מנהל נרשמת כאן
create table if not exists audit_log (
    id          serial primary key,
    action      text not null,
    entity      text not null,
    entity_id   int  not null,
    details     text not null default '',
    actor       text not null default 'מנהל רשת',
    created_at  timestamptz not null default now()
);
alter table audit_log enable row level security;

-- תיעוד נזק (AB#204): תמונה, תיאור ודרגת חומרה מתוך רשימה
create table if not exists damages (
    id           serial primary key,
    unit_id      int  not null references units(id),
    order_id     int  references orders(id),
    severity     text not null check (severity in ('light', 'medium', 'severe')),
    description  text not null,
    photo        text not null,
    created_at   timestamptz not null default now()
);
create index if not exists idx_damages_order on damages(order_id);

-- לוח בקרה למנהל (AB#300): המדדים מחושבים פעם ביום ונשמרים כאן
create table if not exists kpi_daily (
    day        date not null,
    point_id   int  not null default 0,
    data       jsonb not null,
    primary key (day, point_id)
);

alter table damages   enable row level security;
alter table kpi_daily enable row level security;
