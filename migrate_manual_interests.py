#!/usr/bin/env python
"""Migration script to add manual_interests column to User table"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """Add manual_interests column to User table"""
    
    db_path = 'instance/aura.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("DATABASE MIGRATION: Adding manual_interests column")
        print("="*70)
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'manual_interests' in columns:
            print("\n✓ Column 'manual_interests' already exists in User table")
            print("  No migration needed!")
        else:
            print("\n📝 Adding 'manual_interests' column to User table...")
            
            # Add the new column
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN manual_interests TEXT
            """)
            
            conn.commit()
            print("✓ Successfully added 'manual_interests' column")
            
            # Verify the column was added
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'manual_interests' in columns:
                print("✓ Verified: Column exists in database")
            else:
                print("❌ Error: Column was not added")
                return False
        
        # Show current User table structure
        print("\n" + "-"*70)
        print("Current User Table Structure:")
        print("-"*70)
        cursor.execute("PRAGMA table_info(user)")
        for column in cursor.fetchall():
            col_id, name, col_type, not_null, default, pk = column
            print(f"  {name:25} {col_type:15} {'NOT NULL' if not_null else ''}")
        
        conn.close()
        
        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETE")
        print("="*70)
        print("\nThe manual_interests feature is now ready to use!")
        print("Users can now select their preferred news categories in their profile.")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
