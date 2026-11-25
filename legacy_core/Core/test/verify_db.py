import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from Core.data.runtime_paths import CATALOG_DB_PATH

def check():
    conn = sqlite3.connect(CATALOG_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    
    ds_count = conn.execute("SELECT count(*) FROM datasets").fetchone()[0]
    print(f"Total Datasets: {ds_count}")
    
    field_total = 0
    for t in tables:
        if t.startswith('datafields_'):
            count = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            field_total += count
            print(f"{t}: {count} fields")
            
    print(f"Total Fields Across All Regions: {field_total}")
    conn.close()

if __name__ == "__main__":
    check()
