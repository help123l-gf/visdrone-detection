"""Check users table columns"""
from app.config import settings
import psycopg2

conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(r)

# Also check if we can directly query the table
try:
    cur.execute("SELECT * FROM users LIMIT 0")
    cols = [desc[0] for desc in cur.description]
    print("\nDirect query columns:", cols)
except Exception as e:
    print("\nError:", e)

conn.close()
