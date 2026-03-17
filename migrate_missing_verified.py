"""
Migration: Add 'verified' column to missing_person table.
Run once: python migrate_missing_verified.py
"""
import sqlite3
import os

db_path = os.path.join('instance', 'aura.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(missing_person)")
columns = [row[1] for row in cursor.fetchall()]

if 'verified' not in columns:
    cursor.execute("ALTER TABLE missing_person ADD COLUMN verified BOOLEAN NOT NULL DEFAULT 0")
    # Mark all existing cases as verified so they stay visible publicly
    cursor.execute("UPDATE missing_person SET verified = 1 WHERE status IN ('Missing', 'Found')")
    conn.commit()
    print("Migration complete. 'verified' column added.")
    print(f"Existing cases marked as verified: {cursor.rowcount} rows updated.")
else:
    print("Column 'verified' already exists. No changes made.")

conn.close()
