"""
Migration script for BuildCost AI:
Creates `material_storage_properties` reference table in buildcost.db and seeds
initial material shelf-life and storage degradation properties.
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "buildcost.db")


INITIAL_STORAGE_PROPERTIES = [
    (
        "cement",
        75,
        1,
        "Store elevated off the ground, fully sealed in dry covered storage. Moisture absorption causes hydration loss; typical safe window 60–90 days per standard Indian construction site guidance."
    ),
    (
        "steel",
        270,
        1,
        "Store elevated on timber sleepers under waterproof tarpaulins. Surface oxidation tolerates ~9 months per standard structural steel storage guidance before section loss occurs."
    ),
    (
        "sand",
        None,
        0,
        "Fine aggregate tolerates long-term outdoor site storage without structural degradation. Protect from silt contamination and surface runoff."
    ),
    (
        "brick",
        None,
        0,
        "Ceramic masonry bricks tolerate long-term outdoor site storage without structural degradation. Stack on level ground."
    ),
    (
        "gravel",
        None,
        0,
        "Coarse aggregate tolerates long-term outdoor site storage without structural degradation."
    ),
    (
        "wiring",
        None,
        0,
        "PVC insulated copper cables remain stable in dry covered storage for standard construction project durations."
    )
]


def run_migration(db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Executes idempotent migration to support material storage properties.
    """
    if not os.path.exists(db_path):
        print(f"[MIGRATION WARNING] Database not found at {db_path}.")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS material_storage_properties (
                material TEXT PRIMARY KEY,
                max_safe_storage_days INTEGER,
                degrades INTEGER NOT NULL DEFAULT 0,
                storage_notes TEXT NOT NULL
            );
        """)

        for mat, days, degrades, notes in INITIAL_STORAGE_PROPERTIES:
            cursor.execute("""
                INSERT INTO material_storage_properties (material, max_safe_storage_days, degrades, storage_notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(material) DO UPDATE SET
                    max_safe_storage_days=excluded.max_safe_storage_days,
                    degrades=excluded.degrades,
                    storage_notes=excluded.storage_notes;
            """, (mat, days, degrades, notes))

        conn.commit()
        print("[MIGRATION SUCCESS] material_storage_properties table created and seeded successfully.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[MIGRATION ERROR] Failed to run storage properties migration: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
