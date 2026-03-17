import sqlite3
import os

db_path = 'instance/aura.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Current status counts:")
cursor.execute("SELECT status, COUNT(*) FROM advertisement GROUP BY status")
rows = cursor.fetchall()
for row in rows:
    print(f"  {row[0]}: {row[1]}")

# Map old statuses to new statuses
# 'pending' -> 'Pending Payment' or 'Under Review'
# 'approved' -> 'Active'
# 'rejected' -> 'Rejected'

print("\nMigrating statuses...")

# 1. approved -> Active
cursor.execute("UPDATE advertisement SET status = 'Active' WHERE status = 'approved'")
print(f"  Updated {cursor.rowcount} 'approved' to 'Active'")

# 2. rejected -> Rejected
cursor.execute("UPDATE advertisement SET status = 'Rejected' WHERE status = 'rejected'")
print(f"  Updated {cursor.rowcount} 'rejected' to 'Rejected'")

# 3. pending -> Under Review (if payment is pending verification)
cursor.execute("UPDATE advertisement SET status = 'Under Review' WHERE status = 'pending' AND payment_status = 'pending_verification'")
print(f"  Updated {cursor.rowcount} 'pending' (paid) to 'Under Review'")

# 4. pending -> Pending Payment (default for remaining pending)
cursor.execute("UPDATE advertisement SET status = 'Pending Payment' WHERE status = 'pending'")
print(f"  Updated {cursor.rowcount} 'pending' (unpaid) to 'Pending Payment'")

conn.commit()
conn.close()
print("\nMigration completed successfully.")
