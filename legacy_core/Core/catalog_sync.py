"""Explicit catalog synchronization. Authentication/retries belong to BrainClient."""

from Core.api import login, get_day1_universe_map, get_datasets, get_datafields


def sync_catalog(db, *, client=None, skip_datasets=False, skip_fields=False):
    """Synchronize local catalog on explicit invocation; return observable failures."""
    client = client if client is not None else login()
    scopes = get_day1_universe_map(client)
    failures = []
    if not scopes:
        return {"status": "PENDING", "failures": ["SCOPES_UNOBSERVED"]}
    for region, universes in scopes.items():
        for universe in universes:
            try:
                datasets = (db.query_datasets(region=region, universe=universe)
                            if skip_datasets else get_datasets(
                                client, instrument_type="EQUITY", region=region,
                                universe=universe, delay=1))
                if datasets is None or datasets.empty:
                    failures.append(f"{region}/{universe}: DATASETS_UNOBSERVED")
                    continue
                if not skip_datasets:
                    db.upsert_datasets(datasets.to_dict("records"), region, universe)
                if skip_fields:
                    continue
                local = db.query_factors(region=region, universe=universe)
                counts = (local.groupby("dataset_id").size().to_dict()
                          if "dataset_id" in local.columns else {})
                for dataset in datasets.to_dict("records"):
                    dataset_id = dataset["id"]
                    expected = dataset.get("fieldCount")
                    if isinstance(expected, (int, float)) and expected > 0 and counts.get(dataset_id, 0) >= expected:
                        continue
                    fields = get_datafields(client, instrument_type="EQUITY",
                                            region=region, universe=universe,
                                            delay=1, dataset_id=dataset_id)
                    if fields is None or fields.empty:
                        failures.append(f"{region}/{universe}/{dataset_id}: FIELDS_UNOBSERVED")
                        continue
                    db.upsert_datafields(fields.to_dict("records"), region, universe, dataset_id)
                    if isinstance(expected, (int, float)) and len(fields) < expected:
                        failures.append(f"{region}/{universe}/{dataset_id}: FIELDS_PARTIAL")
            except Exception as exc:
                failures.append(f"{region}/{universe}: {type(exc).__name__}")
    return {"status": "PARTIAL" if failures else "COMPLETE", "failures": failures}

