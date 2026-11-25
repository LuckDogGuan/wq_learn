import unittest
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "legacy_core"))

from Core.data.catalog_db import CatalogDB

class TestDataDB(unittest.TestCase):
    def setUp(self):
        # 在临时目录创建一个测试用数据库
        self.test_db_path = Path(__file__).resolve().parent / "test_dummy.db"
        self.db = CatalogDB(db_path=self.test_db_path)

    def test_db_initialization(self):
        # 确保能正常初始化
        with self.db._get_connection() as conn:
            self.assertIsNotNone(conn, "数据库连接应当成功建立")

    def test_table_creation(self):
        # CatalogDB 在 __init__ 时调用了 create_tables() 创建了一张通用的 datasets 表
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='datasets';")
                result = cursor.fetchone()
                self.assertIsNotNone(result, "基础表 datasets 应当成功建立")
        except Exception as e:
            self.fail(f"建表过程抛出异常: {e}")

    def tearDown(self):
        # 清理临时数据库
        if self.test_db_path.exists():
            try:
                os.remove(self.test_db_path)
            except:
                pass

if __name__ == '__main__':
    unittest.main()
