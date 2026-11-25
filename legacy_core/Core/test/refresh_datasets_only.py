import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent.parent))
from Core.catalog.catalog_db import CatalogDB

def main():
    print("Starting background download for DATASETS ONLY (fields skipped)...")
    start_time = time.time()
    
    db = CatalogDB()
    # Passing limit_datasets=0 means it will fetch datasets for all regions/universes,
    # save them to datasets_REGION_UNIVERSE, but then skip fetching the actual datafields.
    db.fetch_all_scopes(limit_datasets=0)
    
    elapsed = time.time() - start_time
    print(f"Datasets refresh completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
