"""
Idempotent migration script for BuildCost AI — Authentication & Per-Engineer Project Scoping:
1. Creates `users` table in buildcost.db if not existing.
2. Adds nullable `user_id` column to `projects` table if not existing.

INTENTIONAL TRADEOFF NOTE ON LEGACY PROJECTS:
Existing projects created prior to authentication rollout have `user_id IS NULL`.
Going forward, authenticated project routes filter strictly by `user_id == current_user.id`.
Therefore, legacy unowned projects (`user_id IS NULL`) will be inaccessible through normal authenticated user routes.
In a production system, a migration script would assign legacy projects to an admin or prompt account owners to claim them.
For this project scope, leaving unowned legacy projects isolated is an intentional design choice.
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "buildcost.db")


def run_migration(db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Executes idempotent migration to support user authentication and project ownership.
    Can be run multiple times safely.
    """
    if not os.path.exists(db_path):
        print(f"[MIGRATION WARNING] Database not found at {db_path}. Will create new database.")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # 1. Create users table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                name TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        print("[MIGRATION SUCCESS] Ensured 'users' table exists.")

        # 2. Ensure projects table exists, then check for user_id column
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects';")
        has_projects = cursor.fetchone() is not None

        if not has_projects:
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
                    notes TEXT,
                    user_id INTEGER REFERENCES users(id)
                );
            """)
            print("[MIGRATION SUCCESS] Created 'projects' table with 'user_id' column.")
        else:
            cursor.execute("PRAGMA table_info(projects);")
            columns = [row[1] for row in cursor.fetchall()]
            if "user_id" not in columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN user_id INTEGER REFERENCES users(id);")
                print("[MIGRATION SUCCESS] Added 'user_id' column to existing projects table.")

        conn.commit()
        print("[MIGRATION SUCCESS] Auth migration finished successfully.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[MIGRATION ERROR] Failed to run auth migration: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
