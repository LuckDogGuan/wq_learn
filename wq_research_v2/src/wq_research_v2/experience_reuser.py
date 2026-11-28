"""Historical Experience Reuse Engine for Route ④ (alphaforge_agy_dsh_v4).

Read-only aggregator over all workspace & user-level WorldQuant BRAIN experience stores:
1. `docs/agents/OPTIMIZATION_LEDGER.json` (`EFF-*` and `INEFF-*` controlled-variable lessons)
2. `wq_research_v2/config/reusable_experience_rules.json` (`IMP-*`, templates, 80:20 stack, invariants)
3. `docs/整理与研究/records/experiments/sc_pass_pc_rescue_queue.json` (historical PC crowding & champions)
4. `~/.gemini/antigravity/skills/worldquant-experience-reuse/references/rules.jsonl` (optional audited rules)

Design principles:
- Strictly read-only: NEVER mutates `reference/`, `OPTIMIZATION_LEDGER.json`, or skill files.
- Scope-aware: matches Region, Universe, Dataset, Neutralization, Failure Code, and Operators,
  preserving narrowest scope, counterexamples, and `transfer_grade` so empirical tendencies are
  never misrepresented as universal laws.
- Compact output: compiles a token-budgeted Experience Context Card (<= 4 KB by default) suitable
  for direct injection into Antigravity CLI (`agy`) prompts and DSH subagent briefs.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from wq_research_v2.config_loader import REPO_ROOT


DEFAULT_LEDGER_JSON = REPO_ROOT / "docs" / "agents" / "OPTIMIZATION_LEDGER.json"
DEFAULT_RULES_JSON = REPO_ROOT / "wq_research_v2" / "config" / "reusable_experience_rules.json"
DEFAULT_PC_QUEUE_JSON = (
    REPO_ROOT / "docs" / "整理与研究" / "records" / "experiments" / "sc_pass_pc_rescue_queue.json"
)
DEFAULT_SKILL_RULES_JSONL = (
    Path.home()
    / ".gemini"
    / "antigravity"
    / "skills"
    / "worldquant-experience-reuse"
    / "references"
    / "rules.jsonl"
)

_FAILURE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "HIGH_PC": ("pc", "prod_correlation", "crowding", "拥挤", "碰撞", "tail", "ram", "reversion_and_momentum"),
    "LOW_2Y_SHARPE": ("2y", "low_2y_sharpe", "is_ladder", "ladder", "近两年", "ts_decay_linear"),
    "LOW_SUB_UNIVERSE_SHARPE": ("sub-uni", "sub_universe", "sub-universe", "adv20", "country*industry", "top1200"),
    "LOW_ASI_JPN_SHARPE": ("jpn", "日本", "low_asi_jpn_sharpe", "asi", "country"),
    "LOW_ROBUST_UNIVERSE": ("robust", "robsh", "robret", "minvol1m", "false=0.5", "false="),
    "HIGH_TURNOVER": ("turnover", "换手", "decay", "hump", "ts_target_tvr_decay"),
    "CONCENTRATED_WEIGHT": ("concentrat", "集中", "weight", "truncation", "winsorize", "quantile"),
    "LOW_FITNESS": ("fitness", "fit", "margin", "turnover", "decay"),
    "PPA_FIRST_TRAP": ("ppa", "ppa-first", "403", "ppac", "8 算子", "3 字段"),
    "TIMEOUT": ("timeout", "超时", "unobserved", "slow_and_fast", "progress=0.35", "sector"),
    "QUICK_FULL_MISMATCH": ("quick", "full", "nanhandling", "1:1", "假象"),
}


def _norm_tokens(text: str) -> set[str]:
    if not text:
        return set()
    return {tok for tok in re.split(r"[^a-z0-9_\u4e00-\u9fff]+", text.lower()) if tok}


def _safe_load_json(path: Optional[Path]) -> Any:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_load_jsonl(path: Optional[Path]) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    items: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            if isinstance(obj, dict):
                items.append(obj)
    except Exception:
        return []
    return items


@dataclass
class ExperienceItem:
    source: str  # OPTIMIZATION_LEDGER | REUSABLE_RULES | SKILL_RULES | PC_QUEUE
    item_id: str
    kind: str  # EFFECTIVE | INEFFECTIVE | EMPIRICAL_RULE | AUDITED_RULE | CROWDING_PRIOR
    score: float
    scope_label: str
    summary: str
    reusable_rule: str
    counterexample_or_caution: str = ""
    transfer_grade: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperiencePacket:
    query: dict[str, Any]
    sources_loaded: dict[str, bool]
    hard_invariants: dict[str, Any]
    knowledge_priority_80_20: list[str]
    effective_lessons: list[ExperienceItem]
    ineffective_warnings: list[ExperienceItem]
    empirical_rules: list[ExperienceItem]
    audited_rules: list[ExperienceItem]
    crowding_priors: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "sources_loaded": self.sources_loaded,
            "hard_invariants": self.hard_invariants,
            "knowledge_priority_80_20": self.knowledge_priority_80_20,
            "effective_lessons": [x.__dict__ for x in self.effective_lessons],
            "ineffective_warnings": [x.__dict__ for x in self.ineffective_warnings],
            "empirical_rules": [x.__dict__ for x in self.empirical_rules],
            "audited_rules": [x.__dict__ for x in self.audited_rules],
            "crowding_priors": self.crowding_priors,
        }

    def render_compact_markdown(self, *, max_bytes: int = 3800) -> str:
        """Render a compact, byte-bounded Experience Context Card for AGY CLI / DSH briefs."""
        q = self.query
        lines: list[str] = [
            f"### 历史经验复用卡（{q.get('region') or 'ALL'}/{q.get('universe') or 'ALL'}/{q.get('dataset_id') or 'ALL'}"
            + (f" · 瓶颈={q['failure_code']}" if q.get("failure_code") else "")
            + "）",
            "- 资料优先级（8:2）：80% 王哥Skill + Top100黄金顾问 + 管理员/课堂53课；20% 仅兜底普通论坛。",
        ]
        if self.effective_lessons:
            lines.append("- **[有效经验（优先复用）]**：")
            for item in self.effective_lessons:
                lines.append(f"  - `{item.item_id}` ({item.scope_label}): {item.reusable_rule}")
        if self.ineffective_warnings:
            lines.append("- **[无效教训与禁区（严禁重演）]**：")
            for item in self.ineffective_warnings:
                lines.append(f"  - `{item.item_id}` ({item.scope_label}): {item.reusable_rule}")
        if self.empirical_rules:
            lines.append("- **[固化提效规则]**：")
            for item in self.empirical_rules:
                caution = f"（注意：{item.counterexample_or_caution}）" if item.counterexample_or_caution else ""
                lines.append(f"  - `{item.item_id}`: {item.reusable_rule}{caution}")
        if self.audited_rules:
            lines.append("- **[跨会话审计规则（含边界与反例）]**：")
            for item in self.audited_rules:
                grade = f"[Grade {item.transfer_grade}]" if item.transfer_grade else ""
                lines.append(f"  - `{item.item_id}` {grade}: {item.summary} → {item.reusable_rule}")
        if self.crowding_priors:
            lines.append("- **[历史拥挤/PC 先验（仅辅助排序，证据不足标 unknown）]**：")
            for cp in self.crowding_priors[:4]:
                lines.append(
                    f"  - `{cp['alpha_id']}` ({cp['region']}/{cp['dataset_id']}, {cp['neutralization']}): "
                    f"status={cp['status']}, SC={cp.get('sc')}, PC={cp.get('pc')}, ge070={cp.get('pc_ge070', 'unknown')}"
                )

        out_lines: list[str] = []
        used = 0
        for ln in lines:
            encoded = (ln + "\n").encode("utf-8")
            if used + len(encoded) > max_bytes:
                out_lines.append("...（已按上下文预算截断，完整条目见 OPTIMIZATION_LEDGER.json 与 reusable_experience_rules.json）")
                break
            out_lines.append(ln)
            used += len(encoded)
        return "\n".join(out_lines)


class ExperienceReuser:
    """Coordinate-aware historical experience retriever across all workspace & skill records."""

    def __init__(
        self,
        *,
        ledger_json_path: Optional[Path] = DEFAULT_LEDGER_JSON,
        rules_json_path: Optional[Path] = DEFAULT_RULES_JSON,
        pc_queue_json_path: Optional[Path] = DEFAULT_PC_QUEUE_JSON,
        skill_rules_jsonl_path: Optional[Path] = DEFAULT_SKILL_RULES_JSONL,
    ) -> None:
        self.ledger_json_path = ledger_json_path
        self.rules_json_path = rules_json_path
        self.pc_queue_json_path = pc_queue_json_path
        self.skill_rules_jsonl_path = skill_rules_jsonl_path

        self.ledger_data = _safe_load_json(ledger_json_path) or {}
        self.rules_data = _safe_load_json(rules_json_path) or {}
        self.pc_queue_data = _safe_load_json(pc_queue_json_path) or {}
        self.skill_rules = _safe_load_jsonl(skill_rules_jsonl_path)

    def sources_status(self) -> dict[str, bool]:
        return {
            "optimization_ledger": bool(self.ledger_data),
            "reusable_experience_rules": bool(self.rules_data),
            "sc_pass_pc_rescue_queue": bool(self.pc_queue_data),
            "worldquant_experience_reuse_skill": bool(self.skill_rules),
        }

    def _score_text(
        self,
        haystack: str,
        *,
        region: str,
        universe: str,
        dataset_id: str,
        neutralization: str,
        failure_code: str,
        operators: Iterable[str],
    ) -> float:
        text_low = (haystack or "").lower()
        tokens = _norm_tokens(text_low)
        score = 0.0

        if region:
            reg = region.lower()
            if reg in tokens or f"{reg}/" in text_low:
                score += 3.0
        if universe and universe.lower() in text_low:
            score += 1.5
        if dataset_id:
            ds = dataset_id.lower()
            if ds in text_low:
                score += 4.5
            else:
                for part in re.split(r"[+_/\s]+", ds):
                    if len(part) >= 3 and part in text_low:
                        score += 2.0
        if neutralization and neutralization.lower() in text_low:
            score += 2.0
        if failure_code:
            fc = failure_code.upper()
            syns = _FAILURE_SYNONYMS.get(fc, (failure_code.lower(),))
            matched_syn = sum(1 for s in syns if s in text_low)
            if matched_syn:
                score += min(4.0, 1.5 * matched_syn)
        for op in operators:
            op_l = op.strip().lower()
            if op_l and op_l in text_low:
                score += 1.5
        return round(score, 2)

    def retrieve(
        self,
        *,
        region: str = "",
        universe: str = "",
        dataset_id: str = "",
        neutralization: str = "",
        failure_code: str = "",
        operators: Optional[Iterable[str]] = None,
        top_eff: int = 4,
        top_ineff: int = 4,
        top_imp: int = 3,
        top_audited: int = 4,
    ) -> ExperiencePacket:
        """Retrieve coordinate-matched effective lessons, bans, empirical rules, and crowding priors."""
        ops = [str(o).strip() for o in (operators or []) if str(o).strip()]
        reg_u = region.strip().upper()
        uni_u = universe.strip().upper()
        ds_s = dataset_id.strip()
        neut_u = neutralization.strip().upper()
        fc_u = failure_code.strip().upper()

        eff_items: list[ExperienceItem] = []
        for idx, case in enumerate(self.ledger_data.get("effective_cases") or []):
            blob = " ".join(
                str(case.get(k) or "")
                for k in ("region_dataset", "controlled_change", "verdict", "metric_delta", "reusable_rule")
            )
            sc = self._score_text(
                blob,
                region=reg_u,
                universe=uni_u,
                dataset_id=ds_s,
                neutralization=neut_u,
                failure_code=fc_u,
                operators=ops,
            )
            if sc > 0 or not (reg_u or ds_s or fc_u or ops):
                # Slight recency tie-breaker (later case_id = more recent verified evidence)
                eff_items.append(
                    ExperienceItem(
                        source="OPTIMIZATION_LEDGER",
                        item_id=str(case.get("case_id") or f"EFF-{idx+1:02d}"),
                        kind="EFFECTIVE",
                        score=round(sc + idx * 0.01, 3),
                        scope_label=str(case.get("region_dataset") or "UNKNOWN")[:64],
                        summary=str(case.get("verdict") or "")[:160],
                        reusable_rule=str(case.get("reusable_rule") or "")[:240],
                        metadata={"metric_delta": str(case.get("metric_delta") or "")[:240]},
                    )
                )
        eff_items.sort(key=lambda x: x.score, reverse=True)

        ineff_items: list[ExperienceItem] = []
        for idx, case in enumerate(self.ledger_data.get("ineffective_cases") or []):
            blob = " ".join(
                str(case.get(k) or "")
                for k in ("region_dataset", "controlled_change", "verdict", "metric_delta", "root_cause_and_ban")
            )
            sc = self._score_text(
                blob,
                region=reg_u,
                universe=uni_u,
                dataset_id=ds_s,
                neutralization=neut_u,
                failure_code=fc_u,
                operators=ops,
            )
            if sc > 0 or not (reg_u or ds_s or fc_u or ops):
                ineff_items.append(
                    ExperienceItem(
                        source="OPTIMIZATION_LEDGER",
                        item_id=str(case.get("case_id") or f"INEFF-{idx+1:02d}"),
                        kind="INEFFECTIVE",
                        score=round(sc + idx * 0.01, 3),
                        scope_label=str(case.get("region_dataset") or "UNKNOWN")[:64],
                        summary=str(case.get("verdict") or "")[:160],
                        reusable_rule=str(case.get("root_cause_and_ban") or "")[:240],
                        metadata={"metric_delta": str(case.get("metric_delta") or "")[:240]},
                    )
                )
        ineff_items.sort(key=lambda x: x.score, reverse=True)

        imp_items: list[ExperienceItem] = []
        for r in self.rules_data.get("factor_improvement_rules_empirical") or []:
            blob = " ".join(
                str(r.get(k) or "") for k in ("rule_id", "symptom", "action", "empirical_evidence", "caution")
            )
            sc = self._score_text(
                blob,
                region=reg_u,
                universe=uni_u,
                dataset_id=ds_s,
                neutralization=neut_u,
                failure_code=fc_u,
                operators=ops,
            )
            if sc > 0 or not (reg_u or ds_s or fc_u or ops):
                imp_items.append(
                    ExperienceItem(
                        source="REUSABLE_RULES",
                        item_id=str(r.get("rule_id") or "IMP"),
                        kind="EMPIRICAL_RULE",
                        score=sc,
                        scope_label="EMPIRICAL_PLAYBOOK",
                        summary=str(r.get("symptom") or "")[:160],
                        reusable_rule=str(r.get("action") or "")[:240],
                        counterexample_or_caution=str(r.get("caution") or "")[:180],
                    )
                )
        imp_items.sort(key=lambda x: x.score, reverse=True)

        audited_items: list[ExperienceItem] = []
        for rule in self.skill_rules:
            scope = rule.get("scope") if isinstance(rule.get("scope"), dict) else {}
            s_regs = [str(x).upper() for x in (scope.get("region") or [])]
            s_ds = [str(x).lower() for x in (scope.get("dataset") or [])]
            s_ops = [str(x).lower() for x in (scope.get("operators") or [])]
            blob = " ".join(
                [
                    str(rule.get("id") or ""),
                    str(rule.get("category") or ""),
                    str(rule.get("rule") or ""),
                    str(rule.get("reuse_instruction") or ""),
                    " ".join(str(c) for c in (rule.get("counterexamples") or [])),
                ]
            )
            sc = self._score_text(
                blob,
                region=reg_u,
                universe=uni_u,
                dataset_id=ds_s,
                neutralization=neut_u,
                failure_code=fc_u,
                operators=ops,
            )
            if reg_u and s_regs and reg_u in s_regs:
                sc += 2.0
            if ds_s and s_ds and ds_s.lower() in s_ds:
                sc += 3.0
            if ops and s_ops and any(o.lower() in s_ops for o in ops):
                sc += 2.5
            # Always keep universal workflow safety/correlation rules accessible when relevant
            if rule.get("generality") == "universal_by_definition" or rule.get("transfer_grade") == "A":
                sc += 0.5
            if sc >= 0.5:
                ce_list = rule.get("counterexamples") or []
                audited_items.append(
                    ExperienceItem(
                        source="SKILL_RULES",
                        item_id=str(rule.get("id") or "rule"),
                        kind="AUDITED_RULE",
                        score=round(sc, 3),
                        scope_label=f"{rule.get('generality', 'unknown')}|regions={','.join(s_regs) or 'ANY'}",
                        summary=str(rule.get("rule") or "")[:180],
                        reusable_rule=str(rule.get("reuse_instruction") or "")[:200],
                        counterexample_or_caution=str(ce_list[0])[:160] if ce_list else "",
                        transfer_grade=str(rule.get("transfer_grade") or "U"),
                    )
                )
        audited_items.sort(key=lambda x: x.score, reverse=True)

        # Crowding priors from sc_pass_pc_rescue_queue.json (read-only)
        crowding_priors = self._extract_crowding_priors(reg_u, ds_s, neut_u)

        primary_80 = [
            str(x.get("source"))
            for x in ((self.rules_data.get("knowledge_lookup_priority_80_20") or {}).get("primary_80_pct") or [])
            if isinstance(x, dict) and x.get("source")
        ]
        hard_invariants = dict(self.rules_data.get("hard_invariants_fixed") or {})

        return ExperiencePacket(
            query={
                "region": reg_u,
                "universe": uni_u,
                "dataset_id": ds_s,
                "neutralization": neut_u,
                "failure_code": fc_u,
                "operators": ops,
            },
            sources_loaded=self.sources_status(),
            hard_invariants=hard_invariants,
            knowledge_priority_80_20=primary_80,
            effective_lessons=eff_items[:top_eff],
            ineffective_warnings=ineff_items[:top_ineff],
            empirical_rules=imp_items[:top_imp],
            audited_rules=audited_items[:top_audited],
            crowding_priors=crowding_priors,
        )

    def _extract_crowding_priors(self, region: str, dataset_id: str, neutralization: str) -> list[dict[str, Any]]:
        """Extract historical SC/PC records for transparent crowding awareness (never fabricates missing PC)."""
        priors: list[dict[str, Any]] = []
        if not isinstance(self.pc_queue_data, dict):
            return priors

        sections = (
            ("USEFUL_OR_OS", self.pc_queue_data.get("useful_all_pass_tagged")),
            ("SC_PASS_QUEUE", self.pc_queue_data.get("sc_pass_pc_rescue_queue")),
            ("SC_PASS_QUEUE", self.pc_queue_data.get("sc_pass_tagged")),
            ("DORMANT_PC", self.pc_queue_data.get("pc_stuck_dormant")),
        )
        for status_group, entries in sections:
            if not isinstance(entries, list):
                continue
            for e in entries:
                if not isinstance(e, dict):
                    continue
                e_reg = str(e.get("region") or "").upper()
                e_ds = str(e.get("dataset_id") or "")
                e_neut = str(e.get("neutralization") or "").upper()
                if region and e_reg and e_reg != region:
                    continue
                if dataset_id and dataset_id.lower() not in e_ds.lower():
                    continue
                if neutralization and e_neut and e_neut != neutralization:
                    continue
                priors.append(
                    {
                        "alpha_id": str(e.get("alpha_id") or "unknown"),
                        "region": e_reg or "unknown",
                        "dataset_id": e_ds or "unknown",
                        "neutralization": e_neut or "unknown",
                        "status": str(e.get("tag") or status_group),
                        "sc": e.get("official_sc") if e.get("official_sc") is not None else e.get("local_sc"),
                        "pc": e.get("remote_pc") if e.get("remote_pc") is not None else e.get("official_pc"),
                        "pc_ge070": e.get("pc_collisions_ge_070", "unknown"),
                        "margin_bp": e.get("margin_bp"),
                    }
                )
        return priors[:10]

    def score_direction_crowding_prior(
        self,
        *,
        region: str,
        dataset_id: str,
        neutralization: str = "",
    ) -> dict[str, Any]:
        """Transparent crowding prior (AlphaForge P2): ranks only from observed evidence, else 'unknown'."""
        priors = self._extract_crowding_priors(region.upper(), dataset_id, neutralization.upper())
        numeric_pcs = [float(p["pc"]) for p in priors if isinstance(p.get("pc"), (int, float))]
        if not numeric_pcs:
            return {
                "region": region.upper(),
                "dataset_id": dataset_id,
                "neutralization": neutralization.upper() or "ANY",
                "sample_count": 0,
                "crowding_level": "UNKNOWN",
                "max_observed_pc": None,
                "note": "证据不足保持 UNKNOWN，仅用于人工排序参考，不替代实盘 PC 查询。",
            }
        max_pc = max(numeric_pcs)
        min_pc = min(numeric_pcs)
        high_cnt = sum(1 for v in numeric_pcs if v >= 0.70)
        if max_pc >= 0.80 and high_cnt == len(numeric_pcs):
            level = "HIGH_CROWDING_PRIOR"
        elif min_pc < 0.70:
            level = "PASSABLE_PRIOR"
        else:
            level = "BORDERLINE_PRIOR"
        return {
            "region": region.upper(),
            "dataset_id": dataset_id,
            "neutralization": neutralization.upper() or "ANY",
            "sample_count": len(numeric_pcs),
            "crowding_level": level,
            "min_observed_pc": round(min_pc, 4),
            "max_observed_pc": round(max_pc, 4),
            "ge_070_samples": high_cnt,
            "note": "透明历史先验（仅辅助排序，实际交付仍以平台实时 numeric PC < 0.70 为准）。",
        }
