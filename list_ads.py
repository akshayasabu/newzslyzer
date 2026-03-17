import sqlite3
import os
db_path = os.path.join('instance', 'aura.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id FROM advertisement LIMIT 5")
print(cursor.fetchall())
conn.close()
