"""
Idempotent migration script for BuildCost AI:
1. Creates `projects` table in buildcost.db if not existing.
2. Adds nullable `project_id` column to `vendor_quotes` table if not existing.
"""

import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "buildcost.db")


def run_migration(db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Executes idempotent migration to support persistent projects.
    Can be run multiple times safely.
    """
    if not os.path.exists(db_path):
        print(f"[MIGRATION WARNING] Database not found at {db_path}. Will create new database.")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # 1. Create projects table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sqft REAL NOT NULL,
                target_materials TEXT NOT NULL,
                region TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                status TEXT DEFAULT 'planning',
                notes TEXT
            );
        """)

        # 3. Create project_phases table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_phases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                phase_name TEXT NOT NULL,
                materials TEXT NOT NULL,
                expected_start_month INTEGER DEFAULT 0,
                status TEXT DEFAULT 'upcoming',
                sequence_order INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
        """)

        # 4. Check vendor_quotes table existence and columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendor_quotes';")
        has_vendor_quotes = cursor.fetchone() is not None

        if not has_vendor_quotes:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vendor_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material TEXT NOT NULL,
                    quoted_rate REAL NOT NULL,
                    quoted_unit TEXT NOT NULL,
                    quoted_date TEXT NOT NULL,
                    source_note TEXT,
                    region TEXT,
                    project_id INTEGER REFERENCES projects(id),
                    phase_id INTEGER REFERENCES project_phases(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            cursor.execute("PRAGMA table_info(vendor_quotes);")
            columns = [row[1] for row in cursor.fetchall()]
            if "project_id" not in columns:
                cursor.execute("ALTER TABLE vendor_quotes ADD COLUMN project_id INTEGER REFERENCES projects(id);")
                print("[MIGRATION SUCCESS] Added 'project_id' column to existing vendor_quotes table.")
            if "phase_id" not in columns:
                cursor.execute("ALTER TABLE vendor_quotes ADD COLUMN phase_id INTEGER REFERENCES project_phases(id);")
                print("[MIGRATION SUCCESS] Added 'phase_id' column to existing vendor_quotes table.")

        conn.commit()
        print("[MIGRATION SUCCESS] Migration finished successfully.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[MIGRATION ERROR] Failed to run migration: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
