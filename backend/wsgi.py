"""נקודת הכניסה לשרת (gunicorn wsgi:app)."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # הרצה מקומית בלי דוקר: python wsgi.py
    app.run(host="0.0.0.0", port=8000, debug=True)
