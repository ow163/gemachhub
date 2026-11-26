"""הרצת 10 בדיקות המערכת ושמירת סיכום עם תאריך ההרצה.

ההרצה הרגילה היא דרך דוקר (ראו README):
    docker compose -f docker-compose.test.yml run --rm e2e

התוצאות נשמרות בתיקייה e2e/results:
    junit.xml   - תוצאה מלאה לכל בדיקה (פורמט JUnit)
    summary.md  - סיכום קצר בעברית: תאריך, כתובת, ותוצאה לכל מקרה בדיקה
"""
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def main():
    RESULTS.mkdir(exist_ok=True)
    started = datetime.now()
    code = pytest.main([str(HERE / "test_system.py"), "-v", "-p", "no:cacheprovider",
                        f"--junitxml={RESULTS / 'junit.xml'}"])

    rows, passed, failed, skipped = [], 0, 0, 0
    for case in ET.parse(RESULTS / "junit.xml").getroot().iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            status, failed = "נכשל", failed + 1
        elif case.find("skipped") is not None:
            status, skipped = "דולג", skipped + 1
        else:
            status, passed = "עבר", passed + 1
        rows.append(f"| {case.get('name')} | {status} | {float(case.get('time', 0)):.1f} |")

    summary = "\n".join([
        "# סיכום הרצת בדיקות מערכת",
        "",
        f"- תאריך ושעת ההרצה: {started:%d/%m/%Y %H:%M}",
        f"- כתובת האתר שנבדק: {os.environ.get('BASE_URL', 'http://localhost:5173')}",
        f"- עברו: {passed} · נכשלו: {failed} · דולגו: {skipped}",
        "",
        "| בדיקה | תוצאה | זמן (שניות) |",
        "|---|---|---|",
        *rows,
        "",
    ])
    (RESULTS / "summary.md").write_text(summary, encoding="utf-8")
    print("\n" + summary)
    return int(code)


if __name__ == "__main__":
    sys.exit(main())
