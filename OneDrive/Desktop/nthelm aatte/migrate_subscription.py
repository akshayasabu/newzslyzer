import sqlite3
import os

def migrate():
    db_path = os.path.join('instance', 'aura.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Migrating database with subscription field...")
        cursor.execute("PRAGMA table_info(user)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'is_subscribed' not in columns:
            print(f"Adding is_subscribed column...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN is_subscribed BOOLEAN DEFAULT 0")
        else:
            print(f"is_subscribed column already exists.")

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
