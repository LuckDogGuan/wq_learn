# -*- coding: utf-8 -*-
"""
alpha_optimizer.py - Automated WorldQuant BRAIN Alpha optimization runner with retry, correlation check, and tracking.
"""
import sys
import time
import asyncio
import json
from pathlib import Path
from cnhkmcp.untracked.platform_functions import BrainApiClient, brain_client, SimulationSettings, SimulationData

async def simulate_with_retry(client: BrainApiClient, sim_data: SimulationData, max_retries: int = 5, retry_delay: float = 12.0):
    await client.ensure_authenticated()
    for attempt in range(1, max_retries + 1):
        try:
            settings_dict = sim_data.settings.model_dump()
            if sim_data.type == "REGULAR":
                settings_dict.pop('selectionHandling', None)
                settings_dict.pop('selectionLimit', None)
                settings_dict.pop('componentActivation', None)
            
            settings_dict = {k: v for k, v in settings_dict.items() if v is not None}
            payload = {
                'type': sim_data.type,
                'settings': settings_dict,
                'regular': sim_data.regular
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            
            resp = client.session.post(f"{client.base_url}/simulations", json=payload)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", retry_delay))
                wait_time = max(retry_after, retry_delay)
                print(f"[{attempt}/{max_retries}] 429 Too Many Requests. Waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            
            resp.raise_for_status()
            location = resp.headers.get('Location', '')
            if not location:
                print(f"[{attempt}/{max_retries}] No location header in response.")
                return None
                
            sim_id = location.split('/')[-1]
            print(f"Simulation created: ID={sim_id}, polling progress...")
            
            while True:
                prog = client.session.get(location)
                if prog.status_code == 429:
                    await asyncio.sleep(5.0)
                    continue
                
                retry_header = prog.headers.get("Retry-After")
                if not retry_header or float(retry_header) == 0:
                    break
                await asyncio.sleep(float(retry_header))
            
            prog_json = prog.json()
            if "alpha" not in prog_json:
                print(f"Simulation completed but no alpha ID found: {prog_json}")
                return None
                
            alpha_id = prog_json["alpha"]
            print(f"Simulation finished! Alpha ID: {alpha_id}")
            alpha_resp = client.session.get(f"{client.base_url}/alphas/{alpha_id}")
            alpha_data = alpha_resp.json()
            return alpha_data
            
        except Exception as e:
            print(f"[{attempt}/{max_retries}] Exception: {e}")
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                raise

async def evaluate_alpha(client: BrainApiClient, alpha_data: dict):
    if not alpha_data or "is" not in alpha_data:
        return None
    
    alpha_id = alpha_data.get("id")
    code = alpha_data.get("regular", {}).get("code", "")
    is_metrics = alpha_data.get("is", {})
    sharpe = is_metrics.get("sharpe", 0.0)
    fitness = is_metrics.get("fitness", 0.0)
    margin = is_metrics.get("margin", 0.0) * 10000.0  # in bp
    turnover = is_metrics.get("turnover", 0.0) * 100.0 # in %
    returns = is_metrics.get("returns", 0.0) * 100.0
    drawdown = is_metrics.get("drawdown", 0.0) * 100.0
    
    checks = is_metrics.get("checks", [])
    failed_checks = [c for c in checks if c.get("result") == "FAIL"]
    warning_checks = [c for c in checks if c.get("result") == "WARNING"]
    
    # 2Y Sharpe
    low_2y = next((c for c in checks if c.get("name") == "LOW_2Y_SHARPE"), None)
    sharpe_2y = low_2y.get("value") if low_2y else None
    
    res = {
        "id": alpha_id,
        "code": code,
        "sharpe": sharpe,
        "fitness": fitness,
        "margin_bp": margin,
        "turnover_pct": turnover,
        "returns_pct": returns,
        "drawdown_pct": drawdown,
        "sharpe_2y": sharpe_2y,
        "failed_checks": [c.get("name") for c in failed_checks],
        "warning_checks": [c.get("name") for c in warning_checks],
        "raw_checks": checks
    }
    
    # Check if eligible for correlation
    # Must have 0 FAIL checks, Sharpe >= 1.25 (or >=1.58 depending on region), Fitness >= 1.0, Turnover between 1% and 70%
    if len(failed_checks) == 0:
        print(f"Alpha {alpha_id} has 0 FAIL checks! Checking correlation...")
        try:
            corr_res = await client.check_correlation(alpha_id, correlation_type="both")
            prod_corr = corr_res.get("checks", {}).get("production", {}).get("max_correlation")
            self_corr = corr_res.get("checks", {}).get("self", {}).get("max_correlation")
            all_passed = corr_res.get("all_passed", False)
            res["prod_corr"] = prod_corr
            res["self_corr"] = self_corr
            res["corr_passed"] = all_passed
            print(f"-> Prod Corr: {prod_corr}, Self Corr: {self_corr}, Passed: {all_passed}")
        except Exception as ce:
            print(f"-> Correlation check error: {ce}")
            res["corr_error"] = str(ce)
    else:
        print(f"Alpha {alpha_id} has FAIL checks: {[c.get('name') for c in failed_checks]}")
    
    return res

if __name__ == "__main__":
    print("alpha_optimizer module ready.")
