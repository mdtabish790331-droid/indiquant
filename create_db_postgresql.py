import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# PostgreSQL connection - APNA PASSWORD YAHAN DAAL
conn = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="pass123",  # <-- CHANGE THIS TO YOUR PASSWORD
    port="5432"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Drop old database if exists and create new
try:
    cur.execute("DROP DATABASE IF EXISTS indiquant_db")
    cur.execute("CREATE DATABASE indiquant_db")
    print("✅ Database 'indiquant_db' created successfully!")
except Exception as e:
    print(f"Error: {e}")
    print("Make sure PostgreSQL is running and password is correct")

cur.close()
conn.close()