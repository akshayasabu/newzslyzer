import sqlite3
import os

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'aura.db')

def migrate_db():
    print(f"Connecting to database at {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database not found. Exiting.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if new columns exist in advertisement table
        cursor.execute("PRAGMA table_info(advertisement)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'duration' not in columns:
            print("Adding 'duration' column to advertisement table...")
            cursor.execute("ALTER TABLE advertisement ADD COLUMN duration INTEGER DEFAULT 7")
            
        if 'payment_details' not in columns:
            print("Adding 'payment_details' column to advertisement table...")
            cursor.execute("ALTER TABLE advertisement ADD COLUMN payment_details VARCHAR(200)")
            
        if 'status' not in columns:
            print("Adding 'status' column to advertisement table...")
            cursor.execute("ALTER TABLE advertisement ADD COLUMN status VARCHAR(20) DEFAULT 'pending'")
            
        # Create AdvertisementChat table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advertisement_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ad_id) REFERENCES advertisement(id),
                FOREIGN KEY(sender_id) REFERENCES user(id)
            )
        """)
        print("Ensured advertisement_chat table exists.")

        # Update existing ads status appropriately if we just added the column
        # Active ads should probably be 'approved' by default, inactive ones 'rejected'
        cursor.execute("UPDATE advertisement SET status = 'approved' WHERE active = 1 AND (status IS NULL OR status = 'pending')")
        cursor.execute("UPDATE advertisement SET status = 'rejected' WHERE active = 0 AND (status IS NULL OR status = 'pending')")
        
        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
