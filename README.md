# GemachHub – רשת גמ"חים קהילתית

מערכת לניהול רשת גמ"חים להשאלת ציוד: קטלוג והזמנה, מסירה והחזרה בנקודות, תרומות ודוחות.
פרויקט בקורס הנדסת תוכנה, מכון לב. **צוות:** אורי וינוגרד (ראש צוות, Product Owner), רפאל זרוק (Scrum Master).

- ניהול הפרויקט (Backlog, ספרינטים, שאילתות, לוחות מעקב, Test Cases, ויקי): https://dev.azure.com/owinogra/GemachHub
- מדריך למשתמש עם צילומי מסך: בוויקי של הפרויקט, בדף "מדריך למשתמש"

## ארכיטקטורה

```
דפדפן ──► frontend (nginx, פורט 5173) ──/api──► backend (Python Flask, פורט 8000) ──► PostgreSQL (Supabase או מקומי)
```

| רכיב | טכנולוגיה | תיקייה |
|---|---|---|
| Frontend | HTML, CSS ו-JavaScript, מוגש על ידי nginx | `frontend/` |
| Backend | Python 3.12, Flask, gunicorn | `backend/` |
| בסיס נתונים | PostgreSQL ב-Supabase (או קונטיינר מקומי), סכמה ונתוני דוגמה | `db/` |
| בדיקות יחידה | pytest (60 בדיקות) | `backend/tests/` |
| בדיקות מערכת | Playwright + pytest (10 בדיקות בדפדפן) | `e2e/` |
| הרצה | Docker Compose | `docker-compose.yml`, `docker-compose.test.yml` |

## מבנה התיקיות

```
gemachhub/
├── docker-compose.yml        # הרצת המערכת: frontend, backend (ו-db מקומי אופציונלי)
├── docker-compose.test.yml   # סביבת הבדיקות: בסיס נתונים נקי, בדיקות יחידה ובדיקות מערכת
├── .env.example              # תבנית למשתני הסביבה (מעתיקים ל-.env)
├── db/
│   ├── schema.sql            # יצירת הטבלאות (אפשר להריץ שוב, לא מוחק נתונים)
│   └── seed.sql              # נתוני דוגמה (מנקה ומכניס מחדש)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt      # תלויות השרת
│   ├── requirements-dev.txt  # תלויות לבדיקות (pytest)
│   ├── wsgi.py               # נקודת הכניסה לשרת
│   ├── app/
│   │   ├── __init__.py       # יצירת האפליקציה ורישום אוטומטי של כל *_routes.py
│   │   ├── db.py             # חיבור לבסיס הנתונים
│   │   ├── booking.py        # כללי הזמנה: שבת וחג, תפיסת יחידות בתאריכים
│   │   ├── notify.py         # שליחת הודעות לשואלים ולתורמים
│   │   └── *_routes.py       # נקודות הקצה של ה-API (טבלה למטה)
│   └── tests/                # בדיקות יחידה
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf            # הגשת האתר והעברת /api ל-backend
│   └── public/               # דפי האתר, css/, js/, img/
├── e2e/
│   ├── test_system.py        # 10 בדיקות המערכת (TC-01 עד TC-10)
│   ├── conftest.py           # הגדרות משותפות לבדיקות
│   ├── run_tests.py          # הרצה ושמירת סיכום עם תאריך ב-e2e/results
│   └── requirements.txt      # pytest ו-playwright
└── .github/                  # תבנית PR ו-CI (בדיקות יחידה, בניית דוקר, בדיקות מערכת)
```

## דרישות מוקדמות

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) (כולל Docker Compose)
2. [Git](https://git-scm.com/downloads)

אין צורך להתקין Python, Node או PostgreSQL. הכול רץ בתוך דוקר.

## הרצת המערכת

### 1. הורדת הקוד
```bash
git clone https://github.com/ow163/gemachhub.git
cd gemachhub
```

### 2. קובץ .env
```bash
cp .env.example .env
```
(ב-Windows PowerShell: `copy .env.example .env`)

הקובץ `.env` מופיע ב-`.gitignore` ולא עולה ל-Git. **אסור לשתף אותו במאגר.** יש שתי אפשרויות לבסיס הנתונים:

**אפשרות א – בסיס נתונים מקומי בדוקר (הכי פשוט, בלי חשבון בענן).**
ב-`.env` מוסיפים `#` בתחילת השורה של אפשרות 1, ומורידים את ה-`#` מהשורה של אפשרות 2:
```
DATABASE_URL=postgresql://gemach:gemach_local_dev@db:5432/gemachhub
```
ומריצים:
```bash
docker compose --profile local-db up --build
```
הסכמה ונתוני הדוגמה נטענים אוטומטית בהרצה הראשונה.

**אפשרות ב – בסיס הנתונים המשותף ב-Supabase.**
1. ב-Supabase, ב-**SQL Editor**, מריצים את התוכן של `db/schema.sql` ואחר כך את `db/seed.sql`.
2. ב-**Project Settings > Database > Connection string** בוחרים **Transaction pooler** ומעתיקים את המחרוזת ל-`DATABASE_URL` ב-`.env`, עם הסיסמה של בסיס הנתונים.
3. מריצים:
```bash
docker compose up --build
```

### 3. פתיחת האתר
- האתר: http://localhost:5173
- בדיקת השרת: http://localhost:8000/api/health

אם בראש מסך הפתיחה כתוב "מחובר לשרת ולבסיס הנתונים", כל התשתית עובדת מקצה לקצה.

עצירה: `Ctrl+C`, ואחר כך `docker compose down`.

### אחרי עדכון של db/schema.sql
- **בסיס נתונים מקומי:** הסקריפטים רצים רק כשהקונטיינר נוצר בפעם הראשונה. כדי לטעון את הסכמה החדשה מוחקים את הנתונים הישנים ומריצים מחדש:
  ```bash
  docker compose --profile local-db down -v
  docker compose --profile local-db up --build
  ```
- **Supabase:** מריצים שוב את `db/schema.sql` ב-SQL Editor (הוא מוסיף רק מה שחסר), ואם רוצים גם נתוני דוגמה נקיים, את `db/seed.sql`.

## בדיקות

כל הבדיקות רצות בדוקר בסביבה נפרדת (`docker-compose.test.yml`). הסביבה מקימה בסיס נתונים חדש ונקי מ-`db/schema.sql` ו-`db/seed.sql` בכל הרצה, ולא נוגעת בקובץ `.env` או ב-Supabase. אין צורך להריץ קודם את המערכת.

### בדיקות יחידה (60 בדיקות של ה-API)
```bash
docker compose -f docker-compose.test.yml run --rm unit-tests
```

### בדיקות מערכת (10 בדיקות Playwright בדפדפן Chromium)
```bash
docker compose -f docker-compose.test.yml run --rm e2e
```
הפקודה בונה ומפעילה את בסיס הנתונים, השרת והאתר, מחכה שכולם יהיו תקינים, ומריצה את הבדיקות מול האתר בכתובת `http://frontend`.
בסוף מוצג סיכום, והוא נשמר גם בקבצים:
- `e2e/results/summary.md` – תאריך ושעת ההרצה ותוצאה לכל בדיקה
- `e2e/results/junit.xml` – תוצאה מלאה בפורמט JUnit

### ניקוי סביבת הבדיקות
```bash
docker compose -f docker-compose.test.yml down
```

### מה כל בדיקת מערכת בודקת

| בדיקה | Test Case | סיפורים | מה נבדק |
|---|---|---|---|
| TC-01 | #426 | #88 | הקטלוג נטען תוך 2 שניות, מספר פריטים לכל קטגוריה, סינון |
| TC-02 | #427 | #93 | חיפוש מתעלם מניקוד ורווחים, הצעת העוזר החכם כשאין תוצאות |
| TC-03 | #428 | #55 | מפת נקודות: פרטי נקודה, שעות וקישור ניווט |
| TC-04 | #429 | #103 | כרטיס פריט: גלריה, פיקדון, תקופת השאלה, זמינות לפי נקודות |
| TC-05 | #430 | #258, #273 | תרומה: תמונה חובה, מספר פנייה, סטטוס והודעה לתורם |
| TC-06 | #431 | #236, #215 | מלאי נקודה לפי סטטוס, רשימת השאלות באיחור ממוינת |
| TC-07 | #432 | #109, #98 | עגלה: הגבלת כמות, סך פיקדון, זמינות לפי תאריכים |
| TC-08 | #433 | #114, #151 | הזמנה: חסימת שבת, מספר הזמנה, ההשאלות שלי |
| TC-09 | #434 | #173, #178, #204, #194 | עמדת מתנדב: איסופים, מסירה, נזק בלי תמונה, קליטת החזרה |
| TC-10 | #435 | #279, #300 | ניהול רשת: דחיית תרומה עם נימוק, לוח KPI תוך 3 שניות |

הבדיקות רצות גם אוטומטית בכל Pull Request (GitHub Actions: `backend-tests`, `docker-build`, `system-tests`).

### הרצת בדיקות המערכת בלי דוקר (למפתחים)
כשהמערכת כבר רצה ב-http://localhost:5173 עם נתוני הדוגמה:
```bash
cd e2e
pip install -r requirements.txt
python -m playwright install chromium
python run_tests.py
```
כתובת אחרת: משתנה הסביבה `BASE_URL` (למשל `BASE_URL=http://localhost:8080`).

## מסכי המערכת

| דף | כתובת | למי |
|---|---|---|
| קטלוג ונקודות, תרומה | `/` | שואלים ותורמים |
| כרטיס פריט | `/item.html?id=<מספר>` | שואלים |
| העגלה שלי והזמנה | `/cart.html` | שואלים |
| ההשאלות שלי | `/loans.html` | שואלים |
| מלאי נקודה | `/inventory.html` | מתנדבים |
| עמדת מתנדב: איסופים, מסירה והחזרה | `/point.html` | מתנדבים |
| השאלות באיחור | `/overdue.html` | מתנדבים |
| ניהול רשת: KPI ותרומות | `/admin.html` | מנהל הרשת |

## נקודות הקצה של ה-API

| שיטה | כתובת | תיאור |
|---|---|---|
| GET | `/api/health` | בדיקת חיבור לשרת ולבסיס הנתונים |
| GET | `/api/points` | נקודות פעילות עם מיקום ושעות פעילות |
| GET | `/api/categories` | קטגוריות עם מספר הפריטים בכל אחת |
| GET | `/api/items?category=&q=&start=&end=&point=` | קטלוג: חיפוש בלי ניקוד, וזמינות בטווח תאריכים ובנקודה |
| GET | `/api/items/<id>` | כרטיס פריט: תמונות, פיקדון וזמינות לפי נקודות |
| POST | `/api/donations` | הצעת תרומה חדשה (תמונה חובה) |
| GET | `/api/donations?limit=5` | הצעות התרומה האחרונות, בלי פרטים אישיים |
| GET | `/api/donations/mine?phone=` | התרומות שלי והסטטוס שלהן |
| POST | `/api/donations/<id>/status` | עדכון סטטוס תרומה (שולח הודעה לתורם) |
| GET | `/api/notifications?phone=` | ההודעות שנשלחו למספר טלפון |
| GET | `/api/points/<id>/inventory?item_id=` | מלאי הנקודה לפי סטטוס |
| GET | `/api/points/<id>/overdue` | השאלות באיחור בנקודה |
| GET, PUT | `/api/cart?phone=` | העגלה שלי, עדכון כמות (0 מוחק) |
| POST | `/api/orders` | יצירת הזמנה: נקודה, תאריכים ושעת איסוף, הקצאת יחידות |
| GET | `/api/loans?phone=` | ההשאלות שלי, כולל איחורים |
| GET | `/api/points/<id>/pickups?date=` | איסופים ליום בנקודה |
| GET | `/api/orders/lookup?point_id=&code=` או `&phone=` | חיפוש הזמנה בנקודה (קוד או סריקת QR) |
| POST | `/api/orders/<id>/handover` | מסירת הזמנה לשואל |
| POST | `/api/orders/<id>/return` | קליטת החזרה, מלאה או חלקית |
| POST | `/api/units/<code>/damage` | תיעוד נזק ביחידה (תמונה חובה) |
| GET | `/api/admin/donations?status=` | תרומות לטיפול המנהל |
| POST | `/api/donations/<id>/decision` | אישור או דחייה של תרומה (דחייה עם נימוק) |
| GET | `/api/admin/audit` | לוג הפעולות של המנהל |
| GET | `/api/admin/kpi?point_id=` | לוח בקרה: מדדים יומיים, לכל הרשת או לנקודה |

## עבודה בצוות: ענפים ו-Pull Requests

ראו [CONTRIBUTING.md](CONTRIBUTING.md). בקצרה: כל שינוי נעשה בענף `feature/<שם>`, ונכנס ל-`main` רק דרך Pull Request שחבר הצוות השני מאשר, אחרי שה-CI עבר.
