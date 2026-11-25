"""Local catalog evaluation helpers; importing never logs in or writes files."""

import logging
import pandas as pd

from Core.data.catalog_db import CatalogDB
from Core.factor.filter.analyzer import categorize_factors

logger = logging.getLogger(__name__)


def get_all_categories_local(db: CatalogDB, region="USA", universe="TOP3000", verbose=False):
    datasets = db.query_datasets(region=region, universe=universe)
    column = next((name for name in ("category_id", "category") if name in datasets), None)
    categories = datasets[column].dropna().unique() if column else []
    if verbose:
        logger.info("%s/%s: %d categories", region, universe, len(categories))
    return datasets, categories


def get_datasets_by_category_local(datasets_df, target_category, verbose=False):
    column = next((name for name in ("category_id", "category") if name in datasets_df), None)
    result = datasets_df[datasets_df[column] == target_category] if column else pd.DataFrame()
    if verbose:
        logger.info("%s: %d datasets", target_category, len(result))
    return result


def evaluate_local_catalog(db, region="USA", universe="TOP3000", category="analyst"):
    """Caller supplies the local database; no remote refresh or report files."""
    datasets, _ = get_all_categories_local(db, region, universe)
    selected = get_datasets_by_category_local(datasets, category)
    reports = {}
    for dataset_id in selected.get("id", []):
        fields = db.query_factors(region=region, universe=universe, dataset_id=dataset_id)
        reports[dataset_id] = categorize_factors(fields) if not fields.empty else {}
    return reports


def main():
    raise SystemExit("请显式传入本地 CatalogDB 调用 evaluate_local_catalog；不会自动创建数据库或联网。")


if __name__ == "__main__":
    main()
