"""SPC-only maintenance; never calls Alpha simulation or submission endpoints."""
import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://api.worldquantbrain.com"
PATH = "/competitions/spc/submissions"
KEYS = {"company_name", "ticker", "isin", "mic", "confidence_score",
        "investment_horizon", "return_prediction"}
STABLE = {"Active", "Active: Stable Output", "Active - Stable Output", "Stable Output"}
BAD = {"Failed", "Unstable Output"}


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_sample(sample):
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
        total = sum((int(ch) * (2 if i % 2 else 1)) // 10 +
                    (int(ch) * (2 if i % 2 else 1)) % 10
                    for i, ch in enumerate(reversed(digits)))
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


def replacement(source, model, version):
    rows = validate_sample(source["sampleOutput"])
    text = source["prompt"].replace("Rank exactly 10 distinct", f"Rank exactly {len(rows)} distinct")
    text = text.replace(
        "Invest only through these empirically-validated themes (each was tested and ranked in cross-sectional backtests on this region):",
        "Evaluate the following research hypotheses; no supporting backtest evidence is supplied:")
    # Preserve the strategy hypotheses without representing historical claims as verified facts.
    text = re.sub(r"(?i)\bBacktests show\b", "The hypothesis is that", text)
    text = re.sub(r"(?i)\bpassed every gate\b", "was previously described as promising", text)
    text += (
        f"\nOutput contract: exactly {len(rows)} objects, with exactly the seven keys specified above. "
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
    return {"name": source["name"] + " | R20261012 " + version,
            "prompt": text, "sampleOutput": source["sampleOutput"], "model": model,
            "modelVersion": version, "weight": "0.00", "updateFrequency": "daily"}


class Client:
    def __init__(self, folder):
        self.folder = Path(folder).resolve()
        if not self.folder.is_relative_to(ROOT / "spc" / "log"):
            raise ValueError("logs must stay inside spc/log")
        self.folder.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        creds = yaml.safe_load((ROOT / "Password/config.yaml").read_text(encoding="utf-8"))
        response = self.session.post(BASE + "/authentication", timeout=45,
                                     auth=(creds["username"], creds["password"]))
        if response.status_code not in (200, 201):
            raise RuntimeError(f"authentication failed: HTTP {response.status_code}")

    def request(self, method, path, payload=None):
        if path != PATH and not re.fullmatch(PATH + r"/[A-Za-z0-9]+", path):
            raise ValueError("SPC endpoint required")
        record = {"time_bjt": now(), "method": method, "path": path, "request": payload}
        journal = self.folder / "operations.jsonl"
        # Write the intent before a mutation, so an interrupted POST can be reconciled.
        if method in {"POST", "PATCH", "DELETE"}:
            with journal.open("a", encoding="utf-8") as f:
                f.write(json.dumps({**record, "phase": "INTENT"}, ensure_ascii=False) + "\n")
        try:
            response = self.session.request(method, BASE + path, json=payload, timeout=45)
        except requests.RequestException as exc:
            with journal.open("a", encoding="utf-8") as f:
                f.write(json.dumps({**record, "phase": "PENDING", "error_type": type(exc).__name__}, ensure_ascii=False) + "\n")
            raise RuntimeError("PENDING: network failure; reconcile without repeating mutations") from None
        try:
            body = response.json()
        except ValueError:
            body = {"non_json": True}
        with journal.open("a", encoding="utf-8") as f:
            f.write(json.dumps({**record, "phase": "RESPONSE", "http_status": response.status_code,
                                "response": body}, ensure_ascii=False) + "\n")
        if not response.ok:
            raise RuntimeError(f"HTTP {response.status_code}: {json.dumps(body, ensure_ascii=False)}")
        return body

    def listing(self):
        rows, offset = [], 0
        while True:
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

    def set_weight(self, identifier, weight):
        before = next(x for x in self.listing() if x["id"] == identifier)
        protected_file = self.folder / "protected_original_stable.json"
        protected = json.loads(protected_file.read_text(encoding="utf-8")) if protected_file.exists() else []
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


def swap(client, plan):
    current = {x["id"]: x for x in client.listing()}
    if current[plan["source_id"]].get("status") in STABLE:
        raise RuntimeError("stable source must be preserved; replacement is forbidden")
    matches = [x for x in current.values() if x["name"] == plan["new_name"]]
    if len(matches) != 1:
        raise RuntimeError("PENDING: replacement ID is missing or ambiguous")
    new = matches[0]
    rows = validate_sample(new["sampleOutput"])
    if (new.get("status") not in STABLE or new["model"] != plan["model"] or
            new["modelVersion"] != plan["modelVersion"] or
            f"Rank exactly {len(rows)} distinct" not in new["prompt"]):
        raise RuntimeError("PENDING: replacement has not passed status/model/output-contract checks")
    old = [current[x] for x in plan["old_active_ids"] if float(current[x]["weight"]) > 0]
    for item in old:
        client.set_weight(item["id"], "0.00")
    try:
        result = client.set_weight(new["id"], "1.00")
    except Exception:
        # Restore only previously stable objects, never reactivate known failed outputs.
        for item in old:
            if item.get("status") in STABLE:
                client.set_weight(item["id"], item["weight"])
        raise
    return {**plan, "new_id": new["id"], "status": result["status"], "weight": result["weight"],
            "verified_at_bjt": now(), "previous_weights": {x["id"]: x["weight"] for x in old}}


def report(client, current):
    folder = client.folder
    initial = json.loads((folder / "list_all.json").read_text(encoding="utf-8"))
    completed = json.loads((folder / "replacements_completed.json").read_text(encoding="utf-8"))
    protected = json.loads((folder / "protected_original_stable.json").read_text(encoding="utf-8"))
    indexed = {x["id"]: x for x in current}
    config_keys = ("id", "name", "prompt", "sampleOutput", "model", "modelVersion", "weight", "updateFrequency")
    preservation = []
    for before in protected:
        after = indexed[before["id"]]
        old_config = {k: before[k] for k in config_keys}
        new_config = {k: after[k] for k in config_keys}
        if old_config != new_config:
            raise RuntimeError("original stable configuration changed: " + before["id"])
        digest = hashlib.sha256(json.dumps(old_config, sort_keys=True).encode()).hexdigest()
        preservation.append({"id": before["id"], "unchanged": True, "config_sha256": digest})
    active = [x for x in current if float(x["weight"]) > 0]
    if len(active) != 50 or any(x["status"] not in STABLE for x in active):
        raise RuntimeError("PENDING: expected 50 platform-stable weighted SPCs")
    if len(completed) != 35 or len({x["new_id"] for x in completed}) != 35:
        raise RuntimeError("PENDING: replacement mapping is incomplete")
    new_ids = {x["new_id"] for x in completed}
    replacements = [indexed[x["new_id"]] for x in completed]
    for item in replacements:
        rows = validate_sample(item["sampleOutput"])
        if item["status"] not in STABLE or float(item["weight"]) != 1:
            raise RuntimeError("PENDING: replacement status changed")
        if f"Rank exactly {len(rows)} distinct" not in item["prompt"]:
            raise RuntimeError("replacement output count mismatch")
    bad_before = [x for x in initial if x["status"] in BAD]
    if any(float(indexed[x["id"]]["weight"]) for x in bad_before):
        raise RuntimeError("a failed/unstable original is still weighted")
    groups = {
        "01_稳定保留/原有活跃15条": [indexed[x["id"]] for x in protected if float(x["weight"]) > 0],
        "01_稳定保留/历史稳定试跑86条": [indexed[x["id"]] for x in protected if float(x["weight"]) == 0],
        "02_替换成功/完整SPC35条": replacements,
        "03_失败停用/原失败10条": [indexed[x["id"]] for x in bad_before if x["status"] == "Failed"],
        "04_不稳定停用/原不稳定25条": [indexed[x["id"]] for x in bad_before if x["status"] == "Unstable Output"],
        "05_稳定备选/未激活的新试跑15条": [x for x in current if " | R20261012 " in x["name"] and x["id"] not in new_ids],
    }
    for label, rows in groups.items():
        save(folder / "分类" / (label + ".json"), {"time_bjt": now(), "count": len(rows), "submissions": rows})
    save(folder / "分类/01_稳定保留/配置未变SHA256.json", preservation)
    save(folder / "分类/02_替换成功/替换对应表.json", completed)
    save(folder / "stable_replacements.json", {"time_bjt": now(), "submissions": replacements})
    save(folder / "stable_active.json", {"time_bjt": now(), "evidence": "SPC list Active = platform stable; underlying supplier routing and raw generated output unavailable", "submissions": active})
    sources = {
        "DeepSeek-V4-Pro-0813": "https://api-docs.deepseek.com/quick_start/pricing/",
        "DeepSeek-V4.1-Flash": "https://api-docs.deepseek.com/api/list-models/",
        "Claude Opus 5.5": "https://www.anthropic.com/claude/opus",
        "GPT-6 Astra": "https://developers.openai.com/api/docs/models/gpt-6-astra",
    }
    new_trials = [x for x in current if " | R20261012 " in x["name"]]
    ledger = []
    for version, source_url in sources.items():
        trials = [x for x in new_trials if x["modelVersion"] == version]
        ledger.append({"model": trials[0]["model"], "spc_modelVersion": version,
                       "official_model_exists": True, "official_source": source_url,
                       "spc_accepted": len(trials), "platform_status_counts": dict(Counter(x["status"] for x in trials)),
                       "activated_replacements": sum(x["id"] in new_ids for x in trials),
                       "evidence_ids": [x["id"] for x in trials], "actual_provider_response_model": "NOT_EXPOSED",
                       "direct_supplier_runs": "NOT_PERFORMED_SPC_STATE_ONLY",
                       "sampleOutput_origin": "inherited schema example, not directly generated provider output"})
    save(folder / "model_ledger.json", {"time_bjt": now(), "models": ledger})
    save(folder / "分类/06_模型核验/model_ledger.json", {"time_bjt": now(), "models": ledger})
    summary = {"time_bjt": now(), "original_total": len(initial), "final_total": len(current),
               "original_stable_unchanged": len(protected), "retained_weighted_originals": 15,
               "replacements": len(replacements), "final_weighted": len(active),
               "final_weighted_statuses": dict(Counter(x["status"] for x in active)),
               "replacement_models": dict(Counter(x["model"] for x in replacements)),
               "deleted_entities": 0, "delete_supported": False, "delete_http_status": 405,
               "disabled_bad_originals": len(bad_before), "stable_new_reserves": len(new_trials) - len(replacements),
               "original_sample_count_warnings": 101, "underlying_model_routing": "NOT_EXPOSED"}
    save(folder / "summary.json", summary)
    lines = ["# SPC 分类记录（2026-10-12，北京时间）", "", f"最终核验：{summary['time_bjt']}", "",
             "原有稳定 SPC 101 条配置均未改动：15 条保持活跃，86 条保持零权重。35 条原失败/不稳定策略已切换到平台标记稳定的修正版。当前权重非零的 50 条均为 Active。", "",
             "**实体删除未完成：平台返回 HTTP 405，禁止 DELETE。旧失败/不稳定对象全部清零，但仍在平台历史中，不能称为已删除。**", "",
             "新激活的 35 条：DeepSeek 19、Claude Opus 5.5 8、GPT-6 Astra 8。另有 15 条新稳定试跑保留零权重作备选，未替换原稳定项。", "",
             "## 分类入口", ""]
    for label, rows in groups.items():
        lines.append(f"- [{label.split('/')[-1]}](分类/{label}.json)：{len(rows)} 条，保留完整 prompt、sampleOutput、模型、状态和权重。")
    lines += ["", "- [稳定活跃 SPC 完整配置](stable_active.json)",
              "- [35 条新稳定替换配置](stable_replacements.json)",
              "- [替换 ID 对应表](分类/02_替换成功/替换对应表.json)",
              "- [模型存在性与 SPC 状态证据](model_ledger.json)",
              "- [逐次变更请求与响应](operations.jsonl)",
              "- [汇总 JSON](summary.json)", "",
              "## 证据边界", "",
              "Active 的稳定含义来自平台 OPTIONS，不代表已经独立多次调用供应商 API。官方资料证实本次四种模型存在；SPC 接受并保持这些配置为 Active，但没有返回实际供应商模型 ID 或生成文本，底层路由未公开。sampleOutput 是继承的格式示例，不能当成供应商实测输出。", "",
              "原有稳定对象的 10 只要求/2 只样例数量警告按用户要求只记录，未改动。新修正版将要求和样例统一为 2 只。稳定状态不证明预测盈利、股票当日可交易或模型真实路由。", "",
              "最初为 50 个策略准备了试跑；用户要求稳定项不变后，停止全量切换。读回核验原有稳定对象未发生修改，其对应的新试跑保持零权重。", ""]
    (folder / "分类记录.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["snapshot", "disable_bad", "create", "activate", "replace", "report"])
    parser.add_argument("--log", required=True)
    parser.add_argument("--payload", help="reviewed JSON file containing replacement payloads")
    parser.add_argument("--id", help="one explicit SPC ID")
    args = parser.parse_args()
    client = Client(args.log)
    current = client.listing()
    if args.action == "report":
        report(client, current)
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d_%H%M%S")
    save(client.folder / ("snapshot_" + stamp + ".json"), current)
    if args.action == "disable_bad":
        targets = [x for x in current if x.get("status") in BAD and float(x["weight"]) > 0]
        save(client.folder / ("disable_plan_" + stamp + ".json"), targets)
        for item in targets:
            result = client.set_weight(item["id"], "0.00")
            print("DISABLED", result["id"], result["status"], flush=True)
    elif args.action == "create":
        payloads = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        for payload in payloads:
            validate_sample(payload["sampleOutput"])
            if payload["weight"] != "0.00":
                raise ValueError("new submissions must start at zero weight")
            matches = [x for x in current if all(x.get(k) == payload[k] for k in
                       ("name", "prompt", "sampleOutput", "model", "modelVersion", "updateFrequency"))]
            if matches:
                print("REUSED", matches[0]["id"], matches[0]["status"], flush=True)
                continue
            result = client.request("POST", PATH, payload)
            if not isinstance(result, dict) or not result.get("id"):
                raise RuntimeError("PENDING: created response has no ID; do not repeat")
            save(client.folder / "created" / (result["id"] + ".json"), result)
            current.append(result)
            print("CREATED", result["id"], result.get("modelVersion"), result.get("status"), flush=True)
    elif args.action == "activate":
        if not args.id:
            parser.error("activate requires one explicit --id")
        result = client.set_weight(args.id, "1.00")
        print("ACTIVATED", result["id"], result["status"], flush=True)
    elif args.action == "replace":
        plans = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        completed = []
        for plan in plans:
            result = swap(client, plan)
            completed.append(result)
            save(client.folder / "replacements_completed.json", completed)
            print("REPLACED", result["source_id"], "->", result["new_id"], result["modelVersion"], flush=True)
    current = client.listing()
    save(client.folder / "latest.json", {"time_bjt": now(), "submissions": current})
    stable = [x for x in current if x.get("status") in STABLE]
    save(client.folder / "platform_stable.json", {"time_bjt": now(), "evidence": "SPC list status only; provider runtime model ID and raw generated outputs are not exposed", "submissions": stable})
    print("TOTAL", len(current), "WEIGHTED", sum(float(x["weight"]) > 0 for x in current),
          "PLATFORM_STABLE", len(stable), flush=True)


if __name__ == "__main__":
    main()
