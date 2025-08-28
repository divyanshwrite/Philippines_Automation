import psycopg2
from config import DB_CONFIG

SUPERUSER = 'divyanshsingh'  # Change if your superuser is different
SUPERPASS = ''          # Set your superuser password here

SQL = """
GRANT USAGE ON SCHEMA source TO fda_user;
GRANT CREATE ON SCHEMA source TO fda_user;
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA source TO fda_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA source GRANT INSERT, UPDATE ON TABLES TO fda_user;
"""

def grant_privileges():
    conn = psycopg2.connect(
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        user=SUPERUSER,
        password=SUPERPASS,
        port=DB_CONFIG['port']
    )
    with conn.cursor() as cur:
        for stmt in SQL.strip().split(';'):
            if stmt.strip():
                cur.execute(stmt)
        conn.commit()
    conn.close()
    print("Privileges granted to fda_user.")

if __name__ == '__main__':
    grant_privileges()
