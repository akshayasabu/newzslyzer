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
        print("Migrating database with new profile fields...")
        cursor.execute("PRAGMA table_info(user)")
        columns = [info[1] for info in cursor.fetchall()]
        
        new_columns = [
            ('first_name', 'TEXT'),
            ('last_name', 'TEXT'),
            ('dob_day', 'TEXT'),
            ('dob_month', 'TEXT'),
            ('dob_year', 'TEXT'),
            ('gender', 'TEXT'),
            ('country', 'TEXT'),
            ('city', 'TEXT')
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                print(f"Adding {col_name} column...")
                cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
            else:
                print(f"{col_name} column already exists.")

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
