"""
api/data_api.py
将平台数据集 (datasets) 和数据字段 (datafields) 的 HTTP 请求从 data/data_fetcher.py 迁移至此。
"""
import time
import pandas as pd
from Core.api.client import BrainClient
from Core.data.catalog_db import CatalogDB


def get_datasets(
    client: BrainClient,
    instrument_type: str = 'EQUITY',
    region: str = 'USA',
    delay: int = 1,
    universe: str = 'TOP3000'
) -> pd.DataFrame:
    """
    从 Brain 平台拉取满足给定维度 (Region, Delay, Universe) 的数据集列表。
    """
    url = (
        f"/data-sets?"
        f"instrumentType={instrument_type}&region={region}"
        f"&delay={delay}&universe={universe}"
    )
    response = client.get(url)
    if not response or response.status_code != 200:
        return pd.DataFrame()
    return pd.DataFrame(response.json().get('results', []))


def get_datafields(
    client: BrainClient,
    instrument_type: str = 'EQUITY',
    region: str = 'USA',
    delay: int = 1,
    universe: str = 'TOP3000',
    dataset_id: str = '',
    search: str = ''
) -> pd.DataFrame:
    """
    分页拉取指定数据集或关键字搜索下的数据字段 (Datafields)。
    内置 429 限流保护与自动重试机制。
    """
    if not search:
        url_template = (
            f"/data-fields?"
            f"&instrumentType={instrument_type}"
            f"&region={region}&delay={delay}&universe={universe}&dataset.id={dataset_id}&limit=50"
            f"&offset={{x}}"
        )
    else:
        url_template = (
            f"/data-fields?"
            f"&instrumentType={instrument_type}"
            f"&region={region}&delay={delay}&universe={universe}&limit=50"
            f"&search={search}&offset={{x}}"
        )

    first_res_resp = client.get(url_template.format(x=0))
    if not first_res_resp or first_res_resp.status_code != 200:
        return pd.DataFrame()
    first_res = first_res_resp.json()
    if 'count' not in first_res:
        return pd.DataFrame()

    count = first_res.get('count', 0) if not search else min(first_res.get('count', 100), 100)
    datafields_list = [first_res.get('results', [])]

    for x in range(50, count, 50):
        resp = client.get(url_template.format(x=x))
        if resp and resp.status_code == 200:
            datafields_list.append(resp.json().get('results', []))
        time.sleep(0.1)

    flat = [item for sublist in datafields_list for item in sublist]
    return pd.DataFrame(flat)


def get_datafield_metadata(
    client: BrainClient,
    field_ids,
    instrument_type: str,
    region: str,
    universe: str,
    delay: int,
    catalog=None,
    read_only=False,
) -> dict:
    """按“候选已存元数据 → 本地 Catalog → 官方接口”解析字段。

    ``catalog`` 可以是已保存的 ``{field_id: metadata}``，也可以是
    :class:`CatalogDB`。返回状态而不是把网络失败误当成字段不存在。
    """
    requested = list(dict.fromkeys(str(item).strip() for item in field_ids if str(item).strip()))
    metadata = {}
    db = catalog if isinstance(catalog, CatalogDB) else None
    if isinstance(catalog, dict):
        metadata.update({
            field_id: dict(catalog[field_id]) for field_id in requested
            if field_id in catalog and isinstance(catalog[field_id], dict)
        })
    if db is None and not read_only:
        try:
            db = CatalogDB()
        except Exception:
            db = None

    unresolved = [field_id for field_id in requested if field_id not in metadata]
    if db is not None and unresolved:
        try:
            local = db.query_factors(region=region, universe=universe)
            if not local.empty and 'id' in local.columns:
                local = local[local['id'].astype(str).isin(unresolved)]
                for record in local.to_dict('records'):
                    metadata[str(record['id'])] = record
        except Exception:
            pass

    unresolved = [field_id for field_id in requested if field_id not in metadata]
    platform_failed = False
    for field_id in unresolved:
        result = get_datafields(
            client,
            instrument_type=instrument_type,
            region=region,
            delay=delay,
            universe=universe,
            search=field_id,
        )
        if result.empty or 'id' not in result.columns:
            platform_failed = True
            continue
        exact = result[result['id'].astype(str) == field_id]
        if exact.empty:
            platform_failed = True
            continue
        record = exact.iloc[0].to_dict()
        metadata[field_id] = record
        if db is not None and not read_only:
            try:
                dataset = record.get('dataset')
                dataset_id = (
                    dataset.get('id') if isinstance(dataset, dict)
                    else record.get('dataset_id') or record.get('dataset.id')
                )
                db.upsert_datafields(
                    [record], region=region, universe=universe, dataset_id=dataset_id
                )
            except Exception:
                pass

    pending = [field_id for field_id in requested if field_id not in metadata]
    return {
        'status': 'PENDING_FIELD_METADATA' if pending or platform_failed else 'OK',
        'metadata': metadata,
        'pending_field_ids': pending,
    }


def get_vec_fields(fields: list) -> list:
    """
    为向量 (VECTOR) 类型字段生成向量聚合算子表达式。
    """
    vec_ops = ["vec_avg", "vec_sum"]
    vec_fields = []
    for field in fields:
        for vec_op in vec_ops:
            if vec_op == "vec_choose":
                vec_fields.append(f"{vec_op}({field}, nth=-1)")
                vec_fields.append(f"{vec_op}({field}, nth=0)")
            else:
                vec_fields.append(f"{vec_op}({field})")
    return vec_fields


def process_datafields(df: pd.DataFrame) -> list:
    """
    从数据字段 DataFrame 提取 MATRIX 和 VECTOR 字段，应用标准预处理模板。
    """
    datafields = []
    datafields += df[df['type'] == "MATRIX"]["id"].tolist()
    datafields += get_vec_fields(df[df['type'] == "VECTOR"]["id"].tolist())
    return [f"winsorize(ts_backfill({f}, 120), std=4)" for f in datafields]
