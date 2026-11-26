"""SPC-only maintenance (modelFamily schema); never calls Alpha simulation or submission endpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

BASE = "https://api.worldquantbrain.com"
PATH = "/competitions/spc/submissions"
KEYS = {
    "company_name",
    "ticker",
    "isin",
    "mic",
    "confidence_score",
    "investment_horizon",
    "return_prediction",
}
STABLE = {"Active", "Active: Stable Output", "Active - Stable Output", "Stable Output"}
BAD = {"Failed", "Unstable Output"}
OUTPUT_CONTRACT_MARKER = "Output contract:"


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "Password" / "config.yaml").exists() or (candidate / ".git").exists():
            return candidate
    return Path(__file__).resolve().parents[3]


ROOT = find_repo_root()


class SPCQuotaExceeded(RuntimeError):
    """Raised when SPC daily or active submission limit is reached."""


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def base_strategy_name(name: str) -> str:
    return name.split(" | ")[0].strip()


def parse_model_catalog(options_body: dict) -> dict[str, dict[str, str]]:
    """Parse OPTIONS /competitions/spc/submissions into {modelFamily_id: metadata}."""
    post_meta = (options_body or {}).get("actions", {}).get("POST", {})
    mf_meta = post_meta.get("modelFamily", {})
    catalog: dict[str, dict[str, str]] = {}
    for group in mf_meta.get("choices", []):
        fam_val = group.get("value", "")
        fam_label = group.get("label", fam_val)
        items = group.get("items") or []
        if items:
            for item in items:
                val = item.get("value")
                if val:
                    catalog[val] = {
                        "family": fam_val,
                        "family_label": fam_label,
                        "label": item.get("label", val),
                    }
        elif fam_val:
            catalog[fam_val] = {
                "family": fam_val,
                "family_label": fam_label,
                "label": fam_label,
            }
    return catalog


def validate_sample(sample: str) -> list[dict]:
    rows = json.loads(sample)
    if not isinstance(rows, list) or not rows:
        raise ValueError("sampleOutput must be a nonempty JSON array")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != KEYS:
            raise ValueError("incorrect output keys")
        for key in ("company_name", "ticker", "isin", "mic"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError("invalid identifier")
        isin = row["isin"]
        if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", isin):
            raise ValueError("invalid ISIN format")
        digits = "".join(str(int(ch, 36)) for ch in isin)
        total = sum(
            (int(ch) * (2 if i % 2 else 1)) // 10 + (int(ch) * (2 if i % 2 else 1)) % 10
            for i, ch in enumerate(reversed(digits))
        )
        if total % 10:
            raise ValueError("invalid ISIN checksum")
        if not re.fullmatch(r"[A-Z0-9]{4}", row["mic"]):
            raise ValueError("invalid MIC format")
        instrument = (isin, row["mic"])
        if instrument in seen:
            raise ValueError("duplicate instrument")
        seen.add(instrument)
        for key in ("confidence_score", "return_prediction"):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]):
                raise ValueError("invalid numeric output")
        if not 0 <= row["confidence_score"] <= 1:
            raise ValueError("confidence outside [0, 1]")
        if type(row["investment_horizon"]) is not int or row["investment_horizon"] <= 0:
            raise ValueError("invalid investment horizon")
    return rows


def replacement(
    source: dict,
    model_family: str,
    model_label: str | None = None,
    *,
    tag: str | None = None,
    update_frequency: str = "daily",
) -> dict:
    """Build an idempotent zero-weight SPC payload using the platform's modelFamily schema."""
    rows = validate_sample(source["sampleOutput"])
    text = re.sub(r"Rank exactly \d+ distinct", f"Rank exactly {len(rows)} distinct", source["prompt"])
    text = text.replace(
        "Invest only through these empirically-validated themes (each was tested and ranked in cross-sectional backtests on this region):",
        "Evaluate the following research hypotheses; no supporting backtest evidence is supplied:",
    )
    text = re.sub(r"(?i)\bBacktests show\b", "The hypothesis is that", text)
    text = re.sub(r"(?i)\bpassed every gate\b", "was previously described as promising", text)
    if OUTPUT_CONTRACT_MARKER not in text:
        text += (
            f"\n{OUTPUT_CONTRACT_MARKER} exactly {len(rows)} objects, with exactly the seven keys specified above. "
            "The sample illustrates schema and numerical scale; it is not verified live market data and "
            "its forecasts are not observed returns. Do not copy sample forecasts as fresh research. "
            "Use only information available as of the evaluation date; never invent a current price, "
            "fundamental value, forecast, insider transaction, backtest result, or identifier. "
            "Research themes are hypotheses, not evidence of profitability. Prefer liquid primary listings; "
            "exclude halted or delisted instruments. Keep a consistent universe and holding-period scale. "
            "When current evidence is unavailable, express a conservative estimate with confidence_score "
            "at most 0.35 and return_prediction 0.0; do not imply fresh market observations. "
            "Use finite JSON numbers, integer positive trading-day horizons, valid ISIN checksums and "
            "exchange MICs. Before returning, validate object count, unique ISIN/MIC pairs, all identifiers, "
            "key names, numerical types and confidence bounds. Return JSON only."
        )
    if len(text) > 10000:
        raise ValueError("prompt exceeds platform maxLength")
    run_tag = tag or ("R" + datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d"))
    label = model_label or model_family
    name = f"{base_strategy_name(source['name'])} | {run_tag} {label}"
    if len(name) > 200:
        raise ValueError("name exceeds platform maxLength")
    return {
        "name": name,
        "prompt": text,
        "sampleOutput": source["sampleOutput"],
        "modelFamily": model_family,
        "weight": "0.00",
        "updateFrequency": update_frequency,
    }


def _allowed_log_roots(root: Path) -> tuple[Path, ...]:
    return (
        (root / "data" / "spc_logs").resolve(),
        (root / "legacy_core" / "pipelines" / "spc" / "log").resolve(),
        (root / "spc" / "log").resolve(),
    )


class Client:
    def __init__(self, folder: str | Path, *, root: Path | None = None):
        self.root = (root or ROOT).resolve()
        self.folder = Path(folder).resolve()
        if not any(self.folder.is_relative_to(allowed) for allowed in _allowed_log_roots(self.root)):
            raise ValueError("logs must stay inside data/spc_logs or legacy_core/pipelines/spc/log")
        self.folder.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.verify = True
        self._authenticate()

    def _authenticate(self) -> None:
        creds = yaml.safe_load((self.root / "Password" / "config.yaml").read_text(encoding="utf-8"))
        response = self.session.post(
            BASE + "/authentication",
            timeout=45,
            auth=(creds["username"], creds["password"]),
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(f"authentication failed: HTTP {response.status_code}")

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if path != PATH and not re.fullmatch(PATH + r"/[A-Za-z0-9]+", path):
            raise ValueError("SPC endpoint required")
        method_up = method.upper()
        record = {"time_bjt": now(), "method": method_up, "path": path, "request": payload}
        journal = self.folder / "operations.jsonl"
        if method_up in {"POST", "PATCH", "DELETE"}:
            with journal.open("a", encoding="utf-8") as f:
                f.write(json.dumps({**record, "phase": "INTENT"}, ensure_ascii=False) + "\n")
        try:
            response = self.session.request(method_up, BASE + path, json=payload, timeout=45)
        except requests.RequestException as exc:
            with journal.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps({**record, "phase": "PENDING", "error_type": type(exc).__name__}, ensure_ascii=False)
                    + "\n"
                )
            raise RuntimeError("PENDING: network failure; reconcile without repeating mutations") from None
        if response.status_code == 401 and method_up in {"GET", "OPTIONS"}:
            self._authenticate()
            response = self.session.request(method_up, BASE + path, json=payload, timeout=45)
        try:
            body = response.json()
        except ValueError:
            body = {"non_json": True, "text": response.text[:500]}
        with journal.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {**record, "phase": "RESPONSE", "http_status": response.status_code, "response": body},
                    ensure_ascii=False,
                )
                + "\n"
            )
        if response.status_code == 429:
            raise SPCQuotaExceeded(f"HTTP 429: {json.dumps(body, ensure_ascii=False)}")
        if not response.ok:
            raise RuntimeError(f"HTTP {response.status_code}: {json.dumps(body, ensure_ascii=False)}")
        return body

    def options(self) -> dict:
        return self.request("OPTIONS", PATH)

    def available_models(self) -> dict[str, dict[str, str]]:
        return parse_model_catalog(self.options())

    def listing(self) -> list[dict]:
        rows, offset = [], 0
        while True:
            response = self.session.get(BASE + PATH, params={"limit": 100, "offset": offset}, timeout=45)
            if response.status_code == 401:
                self._authenticate()
                response = self.session.get(BASE + PATH, params={"limit": 100, "offset": offset}, timeout=45)
            if response.status_code != 200:
                raise RuntimeError(f"PENDING: list HTTP {response.status_code}")
            body = response.json()
            if not isinstance(body, dict) or not isinstance(body.get("results"), list):
                raise RuntimeError("PENDING: incomplete list response")
            rows.extend(body["results"])
            if not body.get("next"):
                if len(rows) != body.get("count") or len({x["id"] for x in rows}) != len(rows):
                    raise RuntimeError("PENDING: pagination drift; do not mutate")
                return rows
            if not body["results"]:
                raise RuntimeError("PENDING: empty page with next")
            offset += len(body["results"])

    def set_weight(self, identifier: str, weight: str, *, allow_protected: bool = False) -> dict:
        before = next(x for x in self.listing() if x["id"] == identifier)
        protected_file = self.folder / "protected_original_stable.json"
        if not allow_protected and protected_file.exists():
            protected = json.loads(protected_file.read_text(encoding="utf-8"))
            if identifier in {x["id"] for x in protected} and float(before["weight"]) != float(weight):
                raise RuntimeError("original stable submissions are protected from modification")
        if weight == "1.00":
            validate_sample(before["sampleOutput"])
            if before.get("status") not in STABLE:
                raise RuntimeError("cannot activate an unverified submission")
        if float(before["weight"]) == float(weight):
            return before
        self.request("PATCH", PATH + "/" + identifier, {"weight": weight})
        after = next(x for x in self.listing() if x["id"] == identifier)
        if float(after["weight"]) != float(weight):
            raise RuntimeError("PENDING: weight readback mismatch")
        return after


def swap(client: Client, plan: dict) -> dict:
    current = {x["id"]: x for x in client.listing()}
    allow_stable = bool(plan.get("allow_stable_upgrade", False))
    source_id = plan.get("source_id")
    if source_id and source_id in current:
        if not allow_stable and current[source_id].get("status") in STABLE:
            raise RuntimeError("stable source must be preserved; replacement is forbidden")

    if plan.get("new_id") and plan["new_id"] in current:
        new = current[plan["new_id"]]
    else:
        matches = [x for x in current.values() if x["name"] == plan["new_name"]]
        if len(matches) != 1:
            raise RuntimeError("PENDING: replacement ID is missing or ambiguous")
        new = matches[0]

    rows = validate_sample(new["sampleOutput"])
    expected_model = plan.get("modelFamily")
    if (
        new.get("status") not in STABLE
        or (expected_model and new.get("modelFamily") != expected_model)
        or f"Rank exactly {len(rows)} distinct" not in new["prompt"]
    ):
        raise RuntimeError("PENDING: replacement has not passed status/modelFamily/output-contract checks")

    old = [current[x] for x in plan.get("old_active_ids", []) if x in current and float(current[x]["weight"]) > 0]
    for item in old:
        client.set_weight(item["id"], "0.00", allow_protected=allow_stable)
    try:
        result = client.set_weight(new["id"], "1.00")
    except Exception:
        # Restore only previously stable objects, never reactivate known failed outputs.
        for item in old:
            if item.get("status") in STABLE:
                client.set_weight(item["id"], item["weight"], allow_protected=True)
        raise
    return {
        **plan,
        "new_id": new["id"],
        "status": result["status"],
        "weight": result["weight"],
        "modelFamily": result.get("modelFamily"),
        "verified_at_bjt": now(),
        "previous_weights": {x["id"]: x["weight"] for x in old},
    }


def summarize(current: list[dict]) -> dict:
    active = [x for x in current if float(x.get("weight", 0)) > 0]
    return {
        "time_bjt": now(),
        "total": len(current),
        "status_counts": dict(Counter(x.get("status") for x in current)),
        "weighted_count": len(active),
        "weighted_statuses": dict(Counter(x.get("status") for x in active)),
        "weighted_models": dict(Counter(x.get("modelFamily") for x in active)),
        "weighted_frequencies": dict(Counter(x.get("updateFrequency") for x in active)),
        "unique_weighted_strategies": len({base_strategy_name(x["name"]) for x in active}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=["snapshot", "options", "disable_bad", "create", "activate", "replace", "audit"],
    )
    parser.add_argument("--log", required=True)
    parser.add_argument("--payload", help="reviewed JSON file containing replacement payloads or swap plans")
    parser.add_argument("--id", help="one explicit SPC ID")
    args = parser.parse_args()

    client = Client(args.log)
    if args.action == "options":
        opt = client.options()
        catalog = parse_model_catalog(opt)
        save(client.folder / "options.json", opt)
        save(client.folder / "model_catalog.json", catalog)
        print("MODELS", len(catalog), flush=True)
        return

    current = client.listing()
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d_%H%M%S")
    save(client.folder / f"snapshot_{stamp}.json", current)

    if args.action == "audit":
        summary = summarize(current)
        save(client.folder / "audit_summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
        return

    if args.action == "disable_bad":
        targets = [x for x in current if x.get("status") in BAD and float(x["weight"]) > 0]
        save(client.folder / f"disable_plan_{stamp}.json", targets)
        for item in targets:
            result = client.set_weight(item["id"], "0.00")
            print("DISABLED", result["id"], result["status"], flush=True)
    elif args.action == "create":
        catalog = client.available_models()
        payloads = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        created_records = []
        for payload in payloads:
            validate_sample(payload["sampleOutput"])
            if payload["weight"] != "0.00":
                raise ValueError("new submissions must start at zero weight")
            if payload.get("modelFamily") not in catalog:
                raise ValueError(f"unsupported modelFamily: {payload.get('modelFamily')}")
            matches = [
                x
                for x in current
                if all(
                    x.get(k) == payload[k]
                    for k in ("name", "prompt", "sampleOutput", "modelFamily", "updateFrequency")
                )
            ]
            if matches:
                print("REUSED", matches[0]["id"], matches[0].get("modelFamily"), matches[0].get("status"), flush=True)
                created_records.append(matches[0])
                continue
            try:
                result = client.request("POST", PATH, payload)
            except SPCQuotaExceeded as exc:
                print("QUOTA_STOP", exc, flush=True)
                break
            if not isinstance(result, dict) or not result.get("id"):
                raise RuntimeError("PENDING: created response has no ID; do not repeat")
            save(client.folder / "created" / f"{result['id']}.json", result)
            current.append(result)
            created_records.append(result)
            print("CREATED", result["id"], result.get("modelFamily"), result.get("status"), flush=True)
        save(client.folder / f"created_batch_{stamp}.json", created_records)
    elif args.action == "activate":
        if not args.id:
            parser.error("activate requires one explicit --id")
        result = client.set_weight(args.id, "1.00")
        print("ACTIVATED", result["id"], result.get("modelFamily"), result["status"], flush=True)
    elif args.action == "replace":
        plans = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        completed_path = client.folder / "replacements_completed.json"
        completed = json.loads(completed_path.read_text(encoding="utf-8")) if completed_path.exists() else []
        for plan in plans:
            result = swap(client, plan)
            completed.append(result)
            save(completed_path, completed)
            print(
                "REPLACED",
                result.get("source_id"),
                "->",
                result["new_id"],
                result.get("modelFamily"),
                result["status"],
                flush=True,
            )

    current = client.listing()
    summary = summarize(current)
    save(client.folder / "latest.json", {"time_bjt": now(), "submissions": current})
    save(client.folder / "audit_summary.json", summary)
    stable = [x for x in current if x.get("status") in STABLE]
    save(
        client.folder / "platform_stable.json",
        {
            "time_bjt": now(),
            "evidence": "SPC list status only; raw generated outputs are not exposed",
            "submissions": stable,
        },
    )
    print(
        "TOTAL",
        summary["total"],
        "WEIGHTED",
        summary["weighted_count"],
        "PLATFORM_STABLE",
        len(stable),
        flush=True,
    )


if __name__ == "__main__":
    main()
