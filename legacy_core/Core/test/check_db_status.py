import sqlite3
import pprint
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from Core.data.runtime_paths import CATALOG_DB_PATH

conn = sqlite3.connect(CATALOG_DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

summary = {}
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    summary[table] = cursor.fetchone()[0]

pprint.pprint(summary)
conn.close()
