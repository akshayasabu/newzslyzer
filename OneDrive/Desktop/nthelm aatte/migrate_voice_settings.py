import sqlite3
import os

def migrate():
    db_path = os.path.join('instance', 'aura.db')
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Migrating database...")
        # Check if columns exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'voice_time' not in columns:
            print("Adding voice_time column...")
            cursor.execute("ALTER TABLE user ADD COLUMN voice_time TEXT")
        else:
            print("voice_time column already exists.")

        if 'voice_enabled' not in columns:
            print("Adding voice_enabled column...")
            cursor.execute("ALTER TABLE user ADD COLUMN voice_enabled BOOLEAN DEFAULT 0")
        else:
            print("voice_enabled column already exists.")

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
