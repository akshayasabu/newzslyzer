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
        print("Migrating SupportMessage table...")
        cursor.execute("PRAGMA table_info(support_message)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'is_read_by_admin' not in columns:
            print("Adding is_read_by_admin column...")
            cursor.execute("ALTER TABLE support_message ADD COLUMN is_read_by_admin BOOLEAN DEFAULT 0")
        else:
            print("is_read_by_admin column already exists.")

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
