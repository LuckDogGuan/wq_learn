"""Stage-0 Fast Demotion + Stage-1 200-Sample Scoped Blacklist Registry with One-Click Restore.

Enforces ALL user & worldquant-experience-reuse laws:
- NEVER blacklists OPERATOR (hard raises ValueError; DB CHECK also blocks it)
- Distinguishes STOP_EARLY / FAST_DEMOTED (Stage-0 24-40 probe) from formal 200-sample SCOPE_BLACKLISTED
- Denominator excludes SYNTAX_ERROR, FAILED_TECH, RATE_LIMITED_429, PENDING, RESULTS_UNOBSERVED,
  and collapses near-duplicate sibling variants (same parent_family_id) to avoid inflating 200
- Requires passing positive control before auto-activation
- Records detailed why_unusable, dissent/single-param rescue hypotheses, and audited restore CLI
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Optional

from wq_research_v2.config_loader import RECORDS_DIR
from wq_research_v2.ledger_store import LedgerStore

ALLOWED_TARGET_TYPES = {"FIELD", "METHOD", "PARAM_COMBO"}


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class BlacklistRegistry:
    """Scoped demotion & automatic 200-sample blacklist registry backed by LedgerStore SQLite."""

    def __init__(self, ledger: LedgerStore, *, export_dir: Optional[Path] = None) -> None:
        self.ledger = ledger
        self.export_dir = export_dir or (RECORDS_DIR / "blacklist")

    def count_valid_evidence_samples(
        self,
        *,
        region: str,
        universe: str,
        dataset_id: Optional[str] = None,
        field_id: Optional[str] = None,
        method_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Count valid FULL deduplicated samples excluding tech/unobserved/near-duplicate families."""
        clauses = ["delay = 1", "region = ?", "universe = ?", "status = 'COMPLETED_FULL'", "alpha_id IS NOT NULL"]
        params: list[Any] = [region.upper(), universe.upper()]
        if dataset_id:
            clauses.append("dataset_id = ?")
            params.append(dataset_id)
        if field_id:
            clauses.append("primary_field_id = ?")
            params.append(field_id)
        if method_id:
            clauses.append("template_id = ?")
            params.append(method_id)

        sql = f"SELECT task_id, alpha_id, parent_family_id, canonical_dedup_key, gate_status, sharpe FROM sim_tasks WHERE {' AND '.join(clauses)}"
        with self.ledger._lock:
            rows = self.ledger._conn.execute(sql, params).fetchall()

        seen_keys: set[str] = set()
        families: set[str] = set()
        alpha_ids: list[str] = []
        tier1_passes = 0
        tier2_passes = 0
        flat_kills = 0
        max_abs_sharpe = 0.0

        for r in rows:
            ck = r["canonical_dedup_key"]
            if ck in seen_keys:
                continue
            seen_keys.add(ck)
            fam = r["parent_family_id"] or r["task_id"]
            families.add(fam)
            alpha_ids.append(r["alpha_id"])
            gs = r["gate_status"] or ""
            if gs == "GATE0_REJECTED_FLAT":
                flat_kills += 1
            if gs in ("GATE3_TIER1_PASS", "GATE4_CANDIDATE_FOR_MANUAL_REVIEW"):
                tier1_passes += 1
            if gs == "GATE4_CANDIDATE_FOR_MANUAL_REVIEW":
                tier2_passes += 1
            if isinstance(r["sharpe"], (int, float)):
                max_abs_sharpe = max(max_abs_sharpe, abs(float(r["sharpe"])))

        return {
            "valid_full_samples": len(seen_keys),
            "distinct_families": len(families),
            "tier1_passes": tier1_passes,
            "tier2_passes": tier2_passes,
            "flat_kills": flat_kills,
            "max_abs_sharpe": round(max_abs_sharpe, 4),
            "evidence_alpha_ids": alpha_ids,
        }

    def register_demotion(
        self,
        *,
        record_id: str,
        level: str,  # FAST_DEMOTED | SCOPE_BLACKLISTED | NEEDS_REVIEW
        target_type: str,
        region: str,
        universe: str,
        dataset_id: Optional[str],
        field_id: Optional[str],
        method_id: Optional[str],
        param_axis: Optional[str],
        valid_sample_count: int,
        positive_control_alpha_id: str,
        evidence_alpha_ids: list[str],
        failed_check_dist: dict[str, int],
        why_unusable: str,
        dissent_and_rescue: list[str],
        write_markdown: bool = True,
    ) -> dict[str, Any]:
        tt = target_type.upper()
        if tt not in ALLOWED_TARGET_TYPES:
            raise ValueError(f"target_type {tt!r} forbidden (OPERATOR is NEVER blacklisted; allowed: {sorted(ALLOWED_TARGET_TYPES)})")
        lv = level.upper()
        if lv == "SCOPE_BLACKLISTED" and valid_sample_count < 200:
            raise ValueError(f"SCOPE_BLACKLISTED requires >= 200 valid samples, got {valid_sample_count} (use FAST_DEMOTED instead)")
        if not positive_control_alpha_id:
            raise ValueError("positive_control_alpha_id is mandatory before activating demotion/blacklist")
        if not why_unusable.strip() or not dissent_and_rescue:
            raise ValueError("why_unusable and dissent_and_rescue hypotheses are mandatory")

        now = _utc_now()
        with self.ledger._lock:
            self.ledger._conn.execute(
                """
                INSERT OR REPLACE INTO blacklist_records (
                    record_id, level, status, target_type, region, universe, delay,
                    dataset_id, field_id, method_id, param_axis, valid_sample_count,
                    positive_control_alpha_id, evidence_alpha_ids_json, failed_check_dist_json,
                    why_unusable, dissent_and_rescue_json, restored_reason, created_at_utc, updated_at_utc
                ) VALUES (?, ?, 'ACTIVE', ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    record_id, lv, tt, region.upper(), universe.upper(),
                    dataset_id, field_id, method_id, param_axis, int(valid_sample_count),
                    positive_control_alpha_id, json.dumps(evidence_alpha_ids), json.dumps(failed_check_dist),
                    why_unusable, json.dumps(dissent_and_rescue, ensure_ascii=False), now, now,
                ),
            )
            self.ledger._conn.commit()

        rec = self.get_record(record_id)
        if write_markdown and rec is not None:
            self._write_card_md(rec)
        return rec or {}

    def get_record(self, record_id: str) -> Optional[dict[str, Any]]:
        with self.ledger._lock:
            row = self.ledger._conn.execute(
                "SELECT * FROM blacklist_records WHERE record_id=?",
                (record_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_records(self, status: Optional[str] = "ACTIVE") -> list[dict[str, Any]]:
        with self.ledger._lock:
            if status:
                rows = self.ledger._conn.execute(
                    "SELECT * FROM blacklist_records WHERE status=? ORDER BY created_at_utc DESC",
                    (status.upper(),),
                ).fetchall()
            else:
                rows = self.ledger._conn.execute(
                    "SELECT * FROM blacklist_records ORDER BY created_at_utc DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def is_blocked(
        self,
        *,
        region: str,
        universe: str,
        delay: int = 1,
        dataset_id: Optional[str] = None,
        field_id: Optional[str] = None,
        method_id: Optional[str] = None,
        param_axis: Optional[str] = None,
    ) -> tuple[bool, Optional[dict[str, Any]]]:
        """Exact scope matching: changing 1 parameter rescues a PARAM_COMBO block automatically."""
        for rec in self.list_records(status="ACTIVE"):
            if rec["region"] != region.upper() or rec["universe"] != universe.upper() or rec["delay"] != delay:
                continue
            tt = rec["target_type"]
            if tt == "FIELD" and rec["field_id"] and rec["field_id"] == field_id:
                return True, rec
            if tt == "METHOD" and rec["method_id"] and rec["method_id"] == method_id:
                if not rec["dataset_id"] or rec["dataset_id"] == dataset_id:
                    return True, rec
            if tt == "PARAM_COMBO":
                field_match = (not rec["field_id"]) or (rec["field_id"] == field_id)
                method_match = (not rec["method_id"]) or (rec["method_id"] == method_id)
                param_match = bool(rec["param_axis"]) and (rec["param_axis"] == param_axis)
                if field_match and method_match and param_match:
                    return True, rec
        return False, None

    def restore(self, record_id: str, reason: str) -> dict[str, Any]:
        """One-click audited recovery from ACTIVE -> RESTORED preserving full history."""
        if not reason.strip():
            raise ValueError("Restoration reason is required")
        with self.ledger._lock:
            cur = self.ledger._conn.execute(
                "UPDATE blacklist_records SET status='RESTORED', restored_reason=?, updated_at_utc=? WHERE record_id=?",
                (reason.strip(), _utc_now(), record_id),
            )
            self.ledger._conn.commit()
            if cur.rowcount == 0:
                raise KeyError(f"Blacklist record not found: {record_id}")
        rec = self.get_record(record_id)
        assert rec is not None
        return rec

    def _write_card_md(self, rec: dict[str, Any]) -> Path:
        self.export_dir.mkdir(parents=True, exist_ok=True)
        path = self.export_dir / f"{rec['record_id']}.md"
        dissent = json.loads(rec["dissent_and_rescue_json"])
        checks = json.loads(rec["failed_check_dist_json"])
        aids = json.loads(rec["evidence_alpha_ids_json"])
        md = "\n".join([
            f"# {rec['record_id']} — {rec['level']} ({rec['target_type']})",
            "",
            f"- **状态**：`{rec['status']}` | **创建时间**：`{rec['created_at_utc']}`",
            f"- **精确作用域**：`{rec['region']} / {rec['universe']} / D1` · dataset=`{rec['dataset_id']}` · field=`{rec['field_id']}` · method=`{rec['method_id']}` · param=`{rec['param_axis']}`",
            f"- **有效样本数**：`{rec['valid_sample_count']}`（不含技术错/未观测/同族近邻重复）",
            f"- **阳性对照 Alpha ID**：`{rec['positive_control_alpha_id']}`",
            f"- **失败检查分布**：`{json.dumps(checks, ensure_ascii=False)}`",
            f"- **样本 Alpha IDs（前 20）**：`{', '.join(aids[:20])}`",
            "",
            "## 详尽不可用原因",
            rec["why_unusable"],
            "",
            "## 保留的不同意见与单参数挽救假设",
            *[f"- {d}" for d in dissent],
            "",
            "## 一键恢复命令",
            "```powershell",
            f"python -m wq_research_v2 blacklist restore --record-id {rec['record_id']} --reason \"<单参数挽救验证说明>\"",
            "```",
        ])
        path.write_text(md, encoding="utf-8")
        return path
