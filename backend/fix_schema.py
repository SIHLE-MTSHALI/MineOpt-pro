import sqlite3
import os

# Using the exact path from database.py logic
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Wait, this script runs from backend, so dirname goes up once
# Actual path: backend/mineopt_pro.db
# Let's just use absolute path directly for clarity

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mineopt_pro.db")

print(f"Target database: {DB_PATH}")
if not os.path.exists(DB_PATH):
    print("ERROR: Database file not found!")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check current columns
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
col_names = [col[1] for col in columns]
print(f"Current columns in users table: {col_names}")

if 'last_login_at' not in col_names:
    print("Adding missing 'last_login_at' column...")
    cursor.execute("ALTER TABLE users ADD COLUMN last_login_at DATETIME")
    conn.commit()
    print("SUCCESS: Column added!")
else:
    print("Column 'last_login_at' already exists.")

conn.close()
print("Done. Please restart your server.")
