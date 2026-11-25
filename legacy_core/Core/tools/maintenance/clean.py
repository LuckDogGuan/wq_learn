import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from Core.data.runtime_paths import CATALOG_DB_PATH


def clean_abnormal_datasets(*, confirmed=False):
    if not confirmed:
        raise RuntimeError("数据库清理需要显式确认")
    with sqlite3.connect(CATALOG_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM datasets WHERE region IS NULL")
        test_datasets = [row[0] for row in cursor.fetchall()]
        if not test_datasets:
            print("No abnormal datasets found.")
            return
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [
            row[0] for row in cursor.fetchall()
            if row[0].startswith("datafields_")
        ]
        for dataset_id in test_datasets:
            for table in tables:
                cursor.execute(
                    f"DELETE FROM {table} WHERE dataset_id = ?", (dataset_id,)
                )
            cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        print(f"Deleted abnormal datasets: {test_datasets}")


if __name__ == "__main__":
    expected = "DELETE ABNORMAL DATASETS"
    if input(f"输入 {expected} 才会继续：").strip() != expected:
        print("Cancelled.")
    else:
        clean_abnormal_datasets(confirmed=True)
