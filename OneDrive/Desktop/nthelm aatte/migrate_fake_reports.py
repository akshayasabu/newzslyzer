"""
Migration: Create fake_report table for tracking community fake reports.
Run once: python migrate_fake_reports.py
"""
import sqlite3, os

db_path = os.path.join('instance', 'aura.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fake_report'")
if cursor.fetchone():
    print("Table 'fake_report' already exists. No changes made.")
else:
    cursor.execute("""
        CREATE TABLE fake_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL REFERENCES missing_person(id) ON DELETE CASCADE,
            user_id INTEGER,
            ip_address VARCHAR(45),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX idx_fake_report_person ON fake_report(person_id)")
    cursor.execute("CREATE INDEX idx_fake_report_user ON fake_report(person_id, user_id)")
    cursor.execute("CREATE INDEX idx_fake_report_ip ON fake_report(person_id, ip_address)")
    conn.commit()
    print("Migration complete. 'fake_report' table created.")

conn.close()
