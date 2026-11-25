import sys
import time
import datetime
import traceback
from pathlib import Path

# 将代码库根目录加入 PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from Core.data.catalog_db import CatalogDB
from Core.data.runtime_paths import CATALOG_DB_PATH, RUNTIME_LOG_DIR

class DualOutput:
    """同时输出到控制台和文件"""
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log_file = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

def main():
    log_dir = RUNTIME_LOG_DIR
    log_dir.mkdir(exist_ok=True)
    
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    log_file_path = log_dir / f"download_{date_str}.log"
    
    # 替换标准输出和标准错误
    dual_logger = DualOutput(log_file_path)
    sys.stdout = dual_logger
    sys.stderr = dual_logger
    
    print("\n=========================================================")
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始后台全网数据同步任务 (支持断点续传)")
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 日志文件保存在: {log_file_path}")
    print("=========================================================\n")
    
    db = CatalogDB(db_path=CATALOG_DB_PATH)
    
    while True:
        try:
            start_time = time.time()
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [STATUS] 正在启动数据拉取流程 fetch_all_scopes()...")
            db.fetch_all_scopes()
            
            elapsed = time.time() - start_time
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SUCCESS] 后台下载顺利完成，耗时 {elapsed:.2f} 秒。")
            break
            
        except Exception as e:
            print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] 下载过程中发生严重错误: {e}")
            traceback.print_exc()
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 将在 5 分钟后自动重试...")
            time.sleep(300)

if __name__ == "__main__":
    main()
