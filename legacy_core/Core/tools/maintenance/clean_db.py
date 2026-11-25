import sqlite3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[3]))
from Core.data.runtime_paths import CATALOG_DB_PATH

def clean_database(*, confirmed=False):
    if not confirmed:
        raise RuntimeError("数据库清理需要显式确认")
    db_path = CATALOG_DB_PATH
    if not db_path.exists():
        print("catalog.db does not exist. Nothing to clean.")
        return

    print("Connecting to catalog.db...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find all datafields tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'datafields_%' OR name LIKE 'datasets%')")
    tables = [row[0] for row in cursor.fetchall()]

    if not tables:
        print("No polluted tables found to clean.")
    else:
        print(f"Found {len(tables)} polluted tables. Dropping them to reset the schema...")
        for table in tables:
            cursor.execute(f"DROP TABLE {table}")
            print(f" - Dropped {table}")
            
    conn.commit()
    conn.close()
    print("Database cleanup complete! The new schema will recreate these tables safely with 'uid'.")

if __name__ == "__main__":
    expected = "DROP CATALOG TABLES"
    if input(f"输入 {expected} 才会继续：").strip() != expected:
        print("Cancelled.")
    else:
        clean_database(confirmed=True)
