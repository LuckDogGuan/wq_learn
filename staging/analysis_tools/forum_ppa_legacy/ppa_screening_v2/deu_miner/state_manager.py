import sqlite3
import json
from .config import DB_PATH

class StateManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Track expressions and their status (PENDING, ERROR, FAIL, PASS_HARD, SUCCESS_POOL)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expressions (
                    expression TEXT,
                    dataset_id TEXT,
                    field_id TEXT,
                    status TEXT,
                    alpha_id TEXT,
                    metrics TEXT,
                    settings TEXT DEFAULT '{}',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (expression, settings)
                )
            ''')
            # Track datasets to avoid repeating
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS datasets (
                    dataset_id TEXT PRIMARY KEY,
                    status TEXT, -- e.g., ACTIVE, EXHAUSTED
                    fields_tested TEXT
                )
            ''')
            # Track global state
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()

    def get_tested_expressions(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT expression FROM expressions")
            return {row[0] for row in cursor.fetchall()}

    def get_success_pool(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT alpha_id, expression, dataset_id FROM expressions WHERE status = 'SUCCESS_POOL'")
            return [{"id": row[0], "expression": row[1], "dataset_id": row[2]} for row in cursor.fetchall()]

    def add_expression(self, expression, dataset_id, field_id, status="PENDING", settings=None):
        settings_str = json.dumps(settings) if settings else '{}'
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO expressions (expression, dataset_id, field_id, status, settings)
                VALUES (?, ?, ?, ?, ?)
            ''', (expression, dataset_id, field_id, status, settings_str))
            conn.commit()
            
    def get_expression_status(self, expression, settings=None):
        settings_str = json.dumps(settings) if settings else '{}'
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM expressions WHERE expression = ? AND settings = ?", (expression, settings_str))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None

    def update_expression(self, expression, status, alpha_id=None, metrics=None, settings=None):
        settings_str = json.dumps(settings) if settings else '{}'
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            metrics_str = json.dumps(metrics) if metrics else None
            cursor.execute('''
                UPDATE expressions 
                SET status = ?, alpha_id = COALESCE(?, alpha_id), metrics = COALESCE(?, metrics)
                WHERE expression = ? AND settings = ?
            ''', (status, alpha_id, metrics_str, expression, settings_str))
            conn.commit()

    def get_active_dataset(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT dataset_id, fields_tested FROM datasets WHERE status = 'ACTIVE' LIMIT 1")
            row = cursor.fetchone()
            if row:
                return {"dataset_id": row[0], "fields_tested": json.loads(row[1]) if row[1] else []}
            return None

    def set_active_dataset(self, dataset_id, fields_tested=None):
        fields_str = json.dumps(fields_tested or [])
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Mark all other active as paused/exhausted if needed, but here we just ensure one active
            cursor.execute("UPDATE datasets SET status = 'EXHAUSTED' WHERE status = 'ACTIVE' AND dataset_id != ?", (dataset_id,))
            cursor.execute('''
                INSERT OR REPLACE INTO datasets (dataset_id, status, fields_tested)
                VALUES (?, 'ACTIVE', ?)
            ''', (dataset_id, fields_str))
            conn.commit()

    def mark_dataset_exhausted(self, dataset_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE datasets SET status = 'EXHAUSTED' WHERE dataset_id = ?", (dataset_id,))
            conn.commit()
