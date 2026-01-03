import sys
from pathlib import Path

# Make sure util is importable (same as your script)
sys.path.append(str(Path(__file__).parent.parent))

from util.db_helper import DBHelper


def main():
    print("=== DB CONTEXT VALIDATION START ===")

    db = DBHelper()
    db.connect()

    cursor = db.get_cursor()

    print("\n--- Connection Identity ---")
    cursor.execute("""
        SELECT
            current_database() AS database,
            current_user AS db_user,
            current_schema() AS schema,
            inet_server_addr() AS server_ip,
            inet_server_port() AS server_port,
            version();
    """)
    print(cursor.fetchone())

    print("\n--- search_path ---")
    cursor.execute("SHOW search_path;")
    print(cursor.fetchone())

    print("\n--- Does table \"User\" exist anywhere? ---")
    cursor.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name = 'User';
    """)
    rows = cursor.fetchall()
    print(rows if rows else "❌ No table named \"User\" found")

    print("\n--- Can we select from public.\"User\" explicitly? ---")
    try:
        cursor.execute('SELECT 1 FROM public."User" LIMIT 1;')
        print("✅ public.\"User\" is accessible")
    except Exception as e:
        print(f"❌ public.\"User\" failed: {e}")

    print("\n--- Can we select from \"User\" without schema? ---")
    try:
        cursor.execute('SELECT 1 FROM "User" LIMIT 1;')
        print("✅ \"User\" is accessible via search_path")
    except Exception as e:
        print(f"❌ \"User\" failed: {e}")

    cursor.close()
    db.close()

    print("\n=== DB CONTEXT VALIDATION END ===")


if __name__ == "__main__":
    main()
