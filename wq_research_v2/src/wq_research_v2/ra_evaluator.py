"""D1-Only 4-Gate Regular Alpha & Power Pool Evaluator.

Implements:
- Gate 0: Flat-PnL "厂字型" kill (<8 active non-zero Sharpe years or >=200 consecutive flat PnL days)
- Gate 1: Signal discovery (IS Sharpe > 0.8; auto sign-flip trigger if Sharpe < -1.2)
- Gate 2: Profitability & regional Margin floor (correctly converts API decimal 0.0010 -> 10.0 bp)
- Gate 3 (Tier-1): Official D1 IS minimum checks (non-CHN vs CHN vs ASI vs ATOM 2Y vs PPA)
- Gate 4 (Tier-2): Local SC pass + remote numeric PC pass + read-only check PASS -> CANDIDATE_FOR_MANUAL_REVIEW
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from wq_research_v2.config_loader import load_d1_thresholds

BLOCKING_WARNING_CHECKS = {"CONCENTRATED_WEIGHT", "LOW_2Y_SHARPE", "IS_LADDER_SHARPE", "LOW_SUB_UNIVERSE_SHARPE"}


def margin_to_bps(margin_decimal: Optional[float]) -> Optional[float]:
    if margin_decimal is None or not math.isfinite(float(margin_decimal)):
        return None
    return round(float(margin_decimal) * 10_000.0, 2)


def detect_flat_pnl_streak(pnl_series: Optional[pd.Series]) -> int:
    """Return longest run of consecutive identical non-zero daily PnL (diff == 0)."""
    if pnl_series is None or len(pnl_series) < 2:
        return 0
    vals = np.asarray(pnl_series.dropna().values, dtype="float64")
    if len(vals) < 2:
        return 0
    diffs = np.diff(vals)
    max_run = 0
    cur = 0
    for d in diffs:
        if abs(d) < 1e-12:
            cur += 1
            if cur > max_run:
                max_run = cur
        else:
            cur = 0
    return max_run


@dataclass
class GateEvaluation:
    alpha_id: str
    region: str
    delay: int
    gate_status: str
    margin_bp: Optional[float]
    meets_regional_margin: bool
    needs_sign_flip: bool
    tier1_passed: bool
    tier2_passed: bool
    failed_checks: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class D1RAEvaluator:
    """Evaluates D1 Regular Alpha (and optional D1 PPA) progression across Gates 0–4."""

    def __init__(self) -> None:
        self.cfg = load_d1_thresholds()
        self.gates = self.cfg["stage_gates"]
        self.margin_floors = self.cfg["regional_margin_floor_decimal"]

    def evaluate(
        self,
        alpha_id: str,
        *,
        region: str,
        delay: int,
        sharpe: Optional[float],
        fitness: Optional[float],
        turnover: Optional[float],
        margin: Optional[float],
        returns: Optional[float] = None,
        long_count: Optional[int] = None,
        short_count: Optional[int] = None,
        active_years: Optional[int] = None,
        max_flat_streak_days: Optional[int] = None,
        is_checks: Optional[list[dict[str, Any]]] = None,
        sc_state: Optional[str] = None,
        pc_status: Optional[str] = None,
        check_status: Optional[str] = None,
        is_ppa: bool = False,
    ) -> GateEvaluation:
        if delay != 1:
            raise ValueError(f"D1-Only violation: delay={delay}")

        reg = region.upper()
        m_bp = margin_to_bps(margin)
        m_floor = float(self.margin_floors.get(reg, 0.0010))
        meets_margin = (margin is not None) and (float(margin) >= m_floor)
        notes: list[str] = []
        failed: list[str] = []

        # Gate 0: Flat-PnL / zero-position kill
        if (long_count is not None and short_count is not None) and (long_count + short_count == 0):
            return GateEvaluation(alpha_id, reg, 1, "GATE0_REJECTED_FLAT", m_bp, meets_margin, False, False, False, ["ZERO_POSITIONS"], ["Zero long+short positions"])
        if active_years is not None and active_years < int(self.gates["gate0_min_active_years"]):
            return GateEvaluation(alpha_id, reg, 1, "GATE0_REJECTED_FLAT", m_bp, meets_margin, False, False, False, ["FLAT_ACTIVE_YEARS"], [f"Active years {active_years} < 8"])
        if max_flat_streak_days is not None and max_flat_streak_days >= int(self.gates["gate0_max_flat_pnl_streak_days"]):
            return GateEvaluation(alpha_id, reg, 1, "GATE0_REJECTED_FLAT", m_bp, meets_margin, False, False, False, ["FLAT_PNL_STREAK"], [f"Flat PnL streak {max_flat_streak_days} >= 200 days"])

        sh = float(sharpe) if sharpe is not None and math.isfinite(float(sharpe)) else None
        fit = float(fitness) if fitness is not None and math.isfinite(float(fitness)) else None
        tvr = float(turnover) if turnover is not None and math.isfinite(float(turnover)) else None
        ret = float(returns) if returns is not None and math.isfinite(float(returns)) else None

        needs_flip = (sh is not None) and (sh < float(self.gates["gate1_auto_flip_sharpe_lt"]))
        if sh is None or sh <= float(self.gates["gate1_sharpe_gt"]):
            if needs_flip:
                notes.append(f"Auto sign-flip trigger: Sharpe {sh:.2f} < -1.20 -> test reverse(expr)")
            return GateEvaluation(alpha_id, reg, 1, "BELOW_GATE1", m_bp, meets_margin, needs_flip, False, False, ["SHARPE_LE_0.8"], notes)

        # Tier-1 official D1 minimum checks
        if is_ppa:
            pp = self.cfg["power_pool_d1"]
            if sh < float(pp["sharpe_ge"]):
                failed.append("PPA_LOW_SHARPE")
        elif reg == "CHN":
            c = self.cfg["regular_d1"]["chn"]
            if sh < float(c["sharpe_ge"]):
                failed.append("CHN_LOW_SHARPE")
            if fit is None or fit < float(c["fitness_ge"]):
                failed.append("CHN_LOW_FITNESS")
            if ret is None or ret < float(c["returns_ge"]):
                failed.append("CHN_LOW_RETURNS")
            if tvr is None or not (float(c["turnover_gt"]) < tvr < float(c["turnover_lt"])):
                failed.append("CHN_TURNOVER")
        else:
            nc = self.cfg["regular_d1"]["non_chn"]
            if sh <= float(nc["sharpe_gt"]):
                failed.append("LOW_SHARPE")
            if fit is None or fit <= float(nc["fitness_gt"]):
                failed.append("LOW_FITNESS")
            if tvr is None or not (float(nc["turnover_gt"]) < tvr < float(nc["turnover_lt"])):
                failed.append("TURNOVER")

        # Inspect platform is.checks (independent of SC/PC)
        for chk in (is_checks or []):
            name = str(chk.get("name", ""))
            res = str(chk.get("result", "")).upper()
            if name in ("SELF_CORRELATION", "PROD_CORRELATION", "POWER_POOL_CORRELATION"):
                continue
            if res == "FAIL":
                failed.append(name)
            elif res == "WARNING" and name in BLOCKING_WARNING_CHECKS:
                failed.append(f"{name}:WARNING")

        if not meets_margin:
            notes.append(f"Margin {m_bp}bp below {reg} empirical floor {m_floor*10000:.0f}bp")

        tier1_pass = len(failed) == 0
        if not tier1_pass:
            gate = "GATE2_IMPROVING" if (ret is None or ret > 0) else "GATE1_POOL_SH08"
            return GateEvaluation(alpha_id, reg, 1, gate, m_bp, meets_margin, False, False, False, failed, notes)

        # Tier-2: SC + remote PC + read-only submission check
        sc_ok = sc_state in ("SC_READY_PASS", "NO_PEERS_IN_REGION")
        pc_ok = pc_status == "PC_READY_PASS"
        chk_ok = check_status in (None, "PASS")
        tier2_pass = sc_ok and pc_ok and chk_ok
        final_gate = "GATE4_CANDIDATE_FOR_MANUAL_REVIEW" if tier2_pass else "GATE3_TIER1_PASS"
        return GateEvaluation(alpha_id, reg, 1, final_gate, m_bp, meets_margin, False, True, tier2_pass, [], notes)
