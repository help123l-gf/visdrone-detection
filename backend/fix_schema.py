"""Fix users table - add missing columns"""
from app.config import settings
import psycopg2

conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

# Add missing columns
cur.execute("""
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255),
    ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS nickname VARCHAR(50),
    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()
""")
conn.commit()
print("Columns added OK")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
print("Users columns:", [r[0] for r in cur.fetchall()])

conn.close()
