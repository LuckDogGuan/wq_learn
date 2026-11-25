import sqlite3
from contextlib import contextmanager
import pandas as pd
from pathlib import Path
from typing import List, Dict, Union
import json
from datetime import datetime, timezone
from Core.data.runtime_paths import CATALOG_DB_PATH

DEFAULT_DB_PATH = CATALOG_DB_PATH


class CatalogDB:
    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()

    @contextmanager
    def _get_connection(self):
        connection = sqlite3.connect(str(self.db_path))
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def create_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Core datasets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY
                )
            ''')
            conn.commit()

    def _normalize_records(self, records: List[Dict]) -> pd.DataFrame:
        if not records:
            return pd.DataFrame()
        df = pd.json_normalize(records, sep="_")
        # SQLite doesn't support lists or dicts natively, convert them to JSON strings
        import json
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
        return df

    def _upsert_dataframe(self, df: pd.DataFrame, table_name: str, primary_key: str):
        if df.empty:
            return
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Ensure the table exists dynamically (for datafields_<REGION>)
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({primary_key} TEXT PRIMARY KEY)")
            
            # Write to a temporary table
            temp_table = f"temp_{table_name}"
            df.to_sql(temp_table, conn, if_exists="replace", index=False)
            
            # Extract temp table columns
            cursor.execute(f"PRAGMA table_info({temp_table})")
            columns = [info[1] for info in cursor.fetchall()]
            
            # Add missing columns to target table
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {info[1] for info in cursor.fetchall()}
            
            for col in columns:
                if col not in existing_columns:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN \"{col}\"")
                    
            # Build UPSERT query
            col_names = ", ".join([f'"{c}"' for c in columns])
            
            # We intentionally exclude `first_written_at` from the DO UPDATE clause 
            # so that it only applies upon initial INSERT.
            excluded_updates = ", ".join([
                f'"{c}" = excluded."{c}"' 
                for c in columns 
                if c != primary_key and c != "first_written_at"
            ])
            
            if excluded_updates:
                upsert_query = f'''
                    INSERT INTO {table_name} ({col_names})
                    SELECT {col_names} FROM {temp_table}
                    WHERE "{primary_key}" IS NOT NULL
                    ON CONFLICT("{primary_key}") DO UPDATE SET {excluded_updates}
                '''
            else:
                upsert_query = f'''
                    INSERT OR IGNORE INTO {table_name} ({col_names})
                    SELECT {col_names} FROM {temp_table}
                    WHERE "{primary_key}" IS NOT NULL
                '''
                
            cursor.execute(upsert_query)
            cursor.execute(f"DROP TABLE {temp_table}")
            conn.commit()

    def upsert_datasets(self, datasets: List[Dict], region: str, universe: str):
        """Upsert a list of dataset dictionaries into the database."""
        df = self._normalize_records(datasets)
        if not df.empty:
            now_str = datetime.now(timezone.utc).isoformat()
            if "first_written_at" not in df.columns:
                df["first_written_at"] = now_str
            df["updated_at"] = now_str
            table_name = f"datasets_{region.upper()}_{universe.upper()}"
            self._upsert_dataframe(df, table_name, "id")

    def upsert_datafields(self, datafields: List[Dict], region: str, universe: str, dataset_id: str = None):
        """Upsert a list of datafield dictionaries into the regional database partition."""
        df = self._normalize_records(datafields)
        if not df.empty:
            if dataset_id and "dataset_id" not in df.columns:
                df["dataset_id"] = dataset_id
                
            now_str = datetime.now(timezone.utc).isoformat()
            if "first_written_at" not in df.columns:
                df["first_written_at"] = now_str
            df["updated_at"] = now_str
            
            table_name = f"datafields_{region.upper()}_{universe.upper()}"
            self._upsert_dataframe(df, table_name, "id")

    def get_all_datasets(self, **filters) -> pd.DataFrame:
        """
        Read datasets from database as DataFrame.
        """
        with self._get_connection() as conn:
            query = "SELECT * FROM datasets"
            params = []
            if filters:
                conditions = []
                for k, v in filters.items():
                    conditions.append(f'"{k}" = ?')
                    params.append(v)
                query += " WHERE " + " AND ".join(conditions)
                
            return pd.read_sql(query, conn, params=params)

    def get_all_datafields(self, region: str = "USA", **filters) -> pd.DataFrame:
        """
        Read datafields from the regional database table as DataFrame.
        """
        table_name = f"datafields_{region.upper()}"
        with self._get_connection() as conn:
            # Check if table exists
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                return pd.DataFrame()
                
            query = f"SELECT * FROM {table_name}"
            params = []
            if filters:
                conditions = []
                for k, v in filters.items():
                    conditions.append(f'"{k}" = ?')
                    params.append(v)
                query += " WHERE " + " AND ".join(conditions)
                
            return pd.read_sql(query, conn, params=params)

    def query_factors(
        self,
        region: str = None,
        universe: str = None,
        category: str = None,
        dataset_id: str = None,
        search: str = None
    ) -> pd.DataFrame:
        """
        高度灵活的统一检索函数。
        根据填写的条件自动跨表查询因子的完整信息（支持全部为空查全库，或填写任意组合查特定因子）。
        
        参数:
        - region: 例如 'USA', 'CHN', 'EUR'
        - universe: 例如 'TOP3000', 'TOP2000U'
        - category: 例如 'Fundamental', 'Analyst', 'Model'
        - dataset_id: 例如 'fundamental31', 'model25'
        - search: 模糊匹配因子 ID 或其描述
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 确定要扫描的目标表 (datafields_REGION_UNIVERSE)
            base_pattern = "datafields_"
            if region:
                base_pattern += f"{region.upper()}_"
            else:
                base_pattern += "%_"
                
            if universe:
                base_pattern += f"{universe.upper()}"
            else:
                base_pattern += "%"
                
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (base_pattern,))
            target_tables = [row[0] for row in cursor.fetchall()]
            
            results = []
            
            # 2. 遍历执行查询
            for df_table in target_tables:
                # 解析出 region 和 universe 以便找到对应的 datasets 表
                parts = df_table.split('_')
                if len(parts) >= 3:
                    curr_region = parts[1]
                    curr_universe = '_'.join(parts[2:])
                else:
                    continue
                    
                ds_table = f"datasets_{curr_region}_{curr_universe}"
                
                # 检查 datasets 表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (ds_table,))
                has_ds = cursor.fetchone() is not None
                
                ds_columns = {row[1] for row in cursor.execute(f'PRAGMA table_info("{ds_table}")')}
                if has_ds and "valueScore" in ds_columns:
                    query = f"SELECT d.*, ds.valueScore FROM {df_table} d LEFT JOIN {ds_table} ds ON d.dataset_id = ds.id WHERE 1=1"
                else:
                    query = f"SELECT d.*, 0 as valueScore FROM {df_table} d WHERE 1=1"
                    
                params = []
                
                if category:
                    query += " AND d.category_name = ?"
                    params.append(category)
                if dataset_id:
                    query += " AND d.dataset_id = ?"
                    params.append(dataset_id)
                if search:
                    query += " AND (d.id LIKE ? OR d.description LIKE ?)"
                    params.extend([f"%{search}%", f"%{search}%"])
                    
                df = pd.read_sql_query(query, conn, params=params)
                if not df.empty:
                    # 确保结果里有 universe 标识
                    if "universe" not in df.columns:
                        df["universe"] = curr_universe
                    results.append(df)
                    
            if not results:
                return pd.DataFrame()
                
            # 合并所有切片的结果
            return pd.concat(results, ignore_index=True)

    def query_datasets(self, region="USA", universe="TOP3000"):
        """Read the same local partition written by upsert_datasets."""
        table = f"datasets_{region.upper()}_{universe.upper()}"
        with self._get_connection() as conn:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not exists:
                return pd.DataFrame()
            quoted = table.replace('"', '""')
            return pd.read_sql_query(f'SELECT * FROM "{quoted}"', conn)

    def fetch_all_scopes(self, skip_datasets: bool = False, skip_fields: bool = False):
        """Compatibility adapter; new callers use Core.catalog_sync.sync_catalog."""
        from Core.catalog_sync import sync_catalog
        return sync_catalog(self, skip_datasets=skip_datasets, skip_fields=skip_fields)

if __name__ == "__main__":
    db = CatalogDB()
    print("Database initialized at:", db.db_path)
