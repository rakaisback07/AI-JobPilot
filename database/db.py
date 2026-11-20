
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "jobpilot.db"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            country TEXT,
            job_type TEXT,
            work_mode TEXT,
            experience TEXT,
            description TEXT,
            apply_url TEXT,
            source TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Saved',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id),
            UNIQUE(job_id)
        )
    """)

    conn.commit()
    conn.close()


def insert_jobs(jobs):
    """Insert new jobs or update existing jobs using external_id."""
    conn = get_connection()

    for job in jobs:
        conn.execute("""
            INSERT INTO jobs (
                external_id, title, company, location, country,
                job_type, work_mode, experience, description,
                apply_url, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_id) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                country = excluded.country,
                job_type = excluded.job_type,
                work_mode = excluded.work_mode,
                experience = excluded.experience,
                description = excluded.description,
                apply_url = excluded.apply_url,
                source = excluded.source
        """, (
            str(job.get("external_id", "")),
            job.get("title", "Untitled"),
            job.get("company", "Unknown"),
            job.get("location", "Not specified"),
            job.get("country", "Not specified"),
            job.get("job_type", "Not specified"),
            job.get("work_mode", "Not specified"),
            job.get("experience", "Not specified"),
            job.get("description", ""),
            job.get("apply_url", ""),
            job.get("source", "Unknown")
        ))

    conn.commit()
    conn.close()


def get_all_jobs():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM jobs ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_job_count():
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]
    conn.close()
    return count


def save_application(job_id):
    conn = get_connection()

    try:
        conn.execute(
            "INSERT INTO applications (job_id) VALUES (?)",
            (job_id,)
        )
        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def get_applications():
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            applications.id AS application_id,
            jobs.id AS job_id,
            jobs.title,
            jobs.company,
            jobs.location,
            jobs.apply_url,
            applications.status,
            applications.notes,
            applications.created_at
        FROM applications
        JOIN jobs ON jobs.id = applications.job_id
        ORDER BY applications.id DESC
    """).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def update_application(application_id, status, notes):
    conn = get_connection()

    conn.execute("""
        UPDATE applications
        SET status = ?, notes = ?
        WHERE id = ?
    """, (status, notes, application_id))

    conn.commit()
    conn.close()


def get_application_count():
    conn = get_connection()

    count = conn.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]

    conn.close()
    return count
