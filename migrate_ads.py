import sqlite3
import os

db_path = 'instance/aura.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE advertisement ADD COLUMN placement VARCHAR(20) DEFAULT 'bottom'")
    print("Added placement column")
except sqlite3.OperationalError as e:
    print(f"Placement column might already exist: {e}")

try:
    cursor.execute("ALTER TABLE advertisement ADD COLUMN is_confirmed BOOLEAN DEFAULT 0")
    print("Added is_confirmed column")
except sqlite3.OperationalError as e:
    print(f"is_confirmed column might already exist: {e}")

conn.commit()
conn.close()
print("Migration completed.")
