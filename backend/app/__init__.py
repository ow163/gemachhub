"""GemachHub API - שרת ה-backend (Flask).

מקבל בקשות מה-frontend וניגש לבסיס הנתונים.
"""
import importlib
import logging
import pkgutil

from flask import Flask, jsonify

from .db import close_conn


def create_app(config=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False  # עברית קריאה בתשובות JSON
    if config:
        app.config.update(config)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # רישום אוטומטי של כל קבצי ה-*_routes.py (כל אחד מגדיר blueprint בשם bp)
    for module_info in pkgutil.iter_modules(__path__):
        if module_info.name.endswith("_routes"):
            module = importlib.import_module(f"{__name__}.{module_info.name}")
            app.register_blueprint(module.bp)
    app.teardown_appcontext(close_conn)

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify(error="הכתובת לא נמצאה"), 404

    return app
