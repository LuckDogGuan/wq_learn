"""运行目录、日志和兼容历史路径。"""

import logging
import os
from datetime import datetime
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import fcntl


HILL_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = str(HILL_ROOT / 'hill_climbing_v4.7')


def create_run_output_dir(base_dir, started_at=None, process_id=None):
    """创建 ``日期/时间_PID`` 运行目录，避免多次启动的日志混在一起。"""
    started_at = started_at or datetime.now()
    process_id = os.getpid() if process_id is None else process_id
    run_dir = os.path.join(
        base_dir, started_at.strftime('%Y-%m-%d'),
        f"{started_at.strftime('%H-%M-%S')}_{process_id}",
    )
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


os.makedirs(OUTPUT_DIR, exist_ok=True)
RUN_OUTPUT_DIR = create_run_output_dir(OUTPUT_DIR)
BASE_CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, 'checkpoint_v4.7.json')
BASE_HISTORY_FILE = os.path.join(OUTPUT_DIR, 'history_v4.7.json')
BASE_DATASET_CACHE_FILE = os.path.join(OUTPUT_DIR, 'dataset_cache_v4.7.json')
BASE_LOG_FILE = os.path.join(RUN_OUTPUT_DIR, 'hill_climbing_v4.7.log')
INSTANCE_LOCK_FILE = os.path.join(OUTPUT_DIR, 'hill_climbing_v4.7.lock')


class SingleInstanceLock:
    """Windows 单实例锁；锁文件可保留，真正互斥由系统文件锁保证。"""

    def __init__(self, path=INSTANCE_LOCK_FILE):
        self.path = str(path)
        self.handle = None
        self.locked = False

    def acquire(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(self.path, 'a+b')
        try:
            self.handle.seek(0)
            if not self.handle.read(1):
                self.handle.write(b'0')
                self.handle.flush()
            self.handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            self.handle = None
            return False
        self.locked = True
        return True

    def release(self):
        if self.handle is None:
            return
        try:
            if self.locked:
                if os.name == "nt":
                    self.handle.seek(0)
                    msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()
            self.handle = None
            self.locked = False


def setup_logging(alpha_id=None):
    log_file = BASE_LOG_FILE if not alpha_id else os.path.join(
        RUN_OUTPUT_DIR, f'{alpha_id}_hill_climbing_v4.7.log'
    )
    for handler in logging.root.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(),
        ],
    )
    logging.info('📢 日志系统已就绪')
    logging.info(f'📁 本次运行日志目录: {os.path.abspath(RUN_OUTPUT_DIR)}')
