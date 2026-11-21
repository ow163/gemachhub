# GemachHub – רשת גמ"חים קהילתית

מערכת לניהול רשת גמ"חים להשאלת ציוד: קטלוג והזמנה, מסירה והחזרה בנקודות, תרומות ודוחות.
פרויקט בקורס הנדסת תוכנה, מכון לב. **צוות:** אורי וינוגרד (ראש צוות, Product Owner), רפאל זרוק (Scrum Master).

- ניהול הפרויקט (Backlog, שאילתות, לוח מעקב, ויקי): https://dev.azure.com/owinogra/GemachHub

## ארכיטקטורה

```
דפדפן ──► frontend (nginx, פורט 5173) ──/api──► backend (Python Flask, פורט 8000) ──► Supabase (PostgreSQL בענן)
```

| רכיב | טכנולוגיה | תיקייה |
|---|---|---|
| Frontend | HTML, CSS ו-JavaScript, מוגש על ידי nginx | `frontend/` |
| Backend | Python 3.12, Flask, gunicorn | `backend/` |
| בסיס נתונים | Supabase (PostgreSQL), סכמה ונתוני דוגמה | `db/` |
| הרצה | Docker Compose | `docker-compose.yml` |

## מבנה התיקיות

```
gemachhub/
├── docker-compose.yml        # הגדרת הקונטיינרים: frontend, backend (ו-db מקומי אופציונלי)
├── .env.example              # תבנית למשתני הסביבה (מעתיקים ל-.env)
├── db/
│   ├── schema.sql            # יצירת הטבלאות
│   └── seed.sql              # נתוני דוגמה
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── wsgi.py               # נקודת הכניסה לשרת
│   ├── app/
│   │   ├── __init__.py       # יצירת האפליקציה ורישום אוטומטי של *_routes.py
│   │   ├── db.py             # חיבור לבסיס הנתונים
│   │   └── core_routes.py    # /api/health, /api/points, /api/categories
│   └── tests/                # בדיקות (pytest)
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf            # הגשת האתר והעברת /api ל-backend
│   └── public/               # index.html, css/, js/
└── .github/                  # תבנית PR ובדיקות אוטומטיות (CI)
```

## דרישות מוקדמות (לכל חבר צוות)

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. [Git](https://git-scm.com/downloads)
3. עורך קוד: VS Code (מומלץ) או PyCharm

## הרצה

### 1. הגדרת בסיס הנתונים ב-Supabase (פעם אחת לכל הצוות)
1. ראש הצוות פותח פרויקט חדש ב-[supabase.com](https://supabase.com) ומזמין את שאר הצוות (Organization > Members).
2. ב-**SQL Editor** מריצים את התוכן של `db/schema.sql` ואחר כך את `db/seed.sql`.
3. ב-**Project Settings > Database > Connection string** בוחרים **Transaction pooler** ומעתיקים את המחרוזת.

### 2. קובץ .env (כל חבר צוות אצלו)
```bash
cp .env.example .env
```
ממלאים ב-`DATABASE_URL` את מחרוזת החיבור מ-Supabase, עם הסיסמה של בסיס הנתונים.
הקובץ `.env` מופיע ב-`.gitignore` ולא עולה ל-Git. **אסור לשתף אותו במאגר.**

### 3. הרצת המערכת
```bash
docker compose up --build
```
- האתר: http://localhost:5173
- ה-API: http://localhost:8000/api/health

אם בראש מסך הפתיחה כתוב "מחובר לשרת ולבסיס הנתונים", כל התשתית עובדת מקצה לקצה.

### עבודה בלי Supabase (בסיס נתונים מקומי)
ב-`.env` משנים את `DATABASE_URL` לשורה של "אפשרות 2", ומריצים:
```bash
docker compose --profile local-db up --build
```
הסכמה ונתוני הדוגמה נטענים אוטומטית בהרצה הראשונה.

## בדיקות

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```
הבדיקות רצות גם אוטומטית בכל Pull Request (GitHub Actions).

## נקודות הקצה של ה-API

| שיטה | כתובת | תיאור |
|---|---|---|
| GET | `/api/health` | בדיקת חיבור לשרת ולבסיס הנתונים |
| GET | `/api/points` | נקודות הגמ"ח הפעילות |
| GET | `/api/categories` | קטגוריות הציוד |
| GET | `/api/items?category=<id>&q=<טקסט>` | קטלוג הפריטים עם מספר היחידות הזמינות (ענף `feature/catalog-items`, אורי) |
| POST | `/api/donations` | שמירת הצעת תרומה חדשה (ענף `feature/donation-offer`, רפאל) |
| GET | `/api/donations?limit=5` | הצעות התרומה האחרונות, בלי פרטים אישיים (ענף `feature/donation-offer`, רפאל) |

## עבודה בצוות: ענפים ו-Pull Requests

ראו [CONTRIBUTING.md](CONTRIBUTING.md). בקצרה: כל שינוי נעשה בענף `feature/<שם>`, ונכנס ל-`main` רק דרך Pull Request שראש הצוות מאשר.
