import sys
from pathlib import Path
import time

# 将代码库根目录加入 PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from Core.api import login
from Core.data.catalog_db import CatalogDB

def main():
    print("Starting background download of all valid regions and universes (Delay=1)...")
    
    db = CatalogDB()
    
    while True:
        try:
            start_time = time.time()
            db.fetch_all_scopes()
            elapsed = time.time() - start_time
            print(f"Background download completed successfully in {elapsed:.2f} seconds.")
            break # Exit loop if successful
        except Exception as e:
            print(f"\n[ERROR] An error occurred during download: {e}")
            print("Sleeping for 5 minutes before retrying...")
            time.sleep(300)

if __name__ == "__main__":
    main()
