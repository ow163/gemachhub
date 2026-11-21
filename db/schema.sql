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
