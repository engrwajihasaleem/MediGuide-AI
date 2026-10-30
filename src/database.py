
import json
import sqlite3

from pathlib import Path
from datetime import datetime, timezone


DB_PATH = Path("data/mediguide_history.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                created_at TEXT NOT NULL,

                language TEXT,

                urgency TEXT,

                symptoms TEXT,

                summary TEXT,

                patient_json TEXT NOT NULL,

                assessment_json TEXT NOT NULL,

                narrative TEXT NOT NULL

            )
        """)


def save_assessment(patient, assessment, narrative):

    created_at = datetime.now(
        timezone.utc
    ).astimezone().isoformat(timespec="seconds")

    with get_connection() as conn:

        cursor = conn.execute(
            """
            INSERT INTO assessments (

                created_at,
                language,
                urgency,
                symptoms,
                summary,
                patient_json,
                assessment_json,
                narrative

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,

            (
                created_at,
                patient.get("language"),
                assessment.get("urgency_level"),
                patient.get("symptoms"),
                assessment.get("summary"),

                json.dumps(
                    patient,
                    ensure_ascii=False
                ),

                json.dumps(
                    assessment,
                    ensure_ascii=False
                ),

                narrative
            )
        )

        return cursor.lastrowid


def get_history(limit=100):

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM assessments
            ORDER BY id DESC
            LIMIT ?
            """,

            (limit,)
        ).fetchall()

    results = []

    for row in rows:

        item = dict(row)

        item["patient"] = json.loads(
            item.pop("patient_json")
        )

        item["assessment"] = json.loads(
            item.pop("assessment_json")
        )

        results.append(item)

    return results


def get_analytics():

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT urgency, COUNT(*) AS total
            FROM assessments
            GROUP BY urgency
            """
        ).fetchall()

    counts = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
        "EMERGENCY": 0
    }

    for row in rows:

        urgency = row["urgency"]

        if urgency in counts:
            counts[urgency] = row["total"]

    return counts


def delete_history():

    with get_connection() as conn:

        conn.execute(
            "DELETE FROM assessments"
        )
