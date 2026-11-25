import time
import asyncio
import sqlite3
import yaml
import os
import json
from .config import SETTINGS
from .state_manager import StateManager
from .network import BrainAPI
import sys
import importlib
from . import alpha_generator
from .evaluator import evaluate_metrics, evaluate_neutralized, generate_diversity_report
from cnhkmcp.untracked.platform_functions import create_multi_simulation, authenticate

class MinerRunner:
    def __init__(self):
        self.state = StateManager()
        self.api = BrainAPI()  # for other api calls if needed
        self.datasets = alpha_generator.load_datefields_datasets()
        
        # Use explicit absolute path or robust relative path
        cred_path = r'D:\code\WorldQuant Brain\goal\Password\config.yaml'
        cred = yaml.safe_load(open(cred_path, encoding='utf-8'))
        asyncio.run(authenticate(cred['username'], cred['password']))

        
    def get_or_pick_active_dataset(self):
        active = self.state.get_active_dataset()
        if active:
            return active['dataset_id'], active['fields_tested']
        
        # Pick a new one
        for ds_id in self.datasets:
            # check if exhausted in db
            with sqlite3.connect(self.state.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM datasets WHERE dataset_id = ?", (ds_id,))
                row = cursor.fetchone()
                if not row or row[0] != 'EXHAUSTED':
                    self.state.set_active_dataset(ds_id, [])
                    return ds_id, []
        return None, []

    def simulate_batch(self, exprs, settings_override=None):
        settings_override = settings_override or {}
        expressions_only = [item['expression'] for item in exprs]
        
        # WorldQuant BRAIN API requires at least 2 expressions per multi_simulation batch
        if len(expressions_only) == 1:
            expressions_only.append("rank(close)")
            
        try:
            res = asyncio.run(create_multi_simulation(
                alpha_expressions=expressions_only,
                instrument_type=settings_override.get('instrumentType', SETTINGS['instrumentType']),
                region=settings_override.get('region', SETTINGS['region']),
                universe=settings_override.get('universe', SETTINGS['universe']),
                delay=settings_override.get('delay', SETTINGS['delay']),
                decay=settings_override.get('decay', SETTINGS.get('decay', 0)),
                neutralization=settings_override.get('neutralization', SETTINGS['neutralization']),
                truncation=settings_override.get('truncation', SETTINGS.get('truncation', 0.08)),
                pasteurization=settings_override.get('pasteurization', SETTINGS.get('pasteurize', 'ON')),
                unit_handling=settings_override.get('unitHandling', SETTINGS.get('unitHandling', 'VERIFY')),
                nan_handling=settings_override.get('nanHandling', SETTINGS.get('nanHandling', 'OFF')),
                language=settings_override.get('language', SETTINGS.get('language', 'FASTEXPR')),
                visualization=SETTINGS.get('visualization', False),
                max_trade='OFF'
            ))
        except Exception as e:
            print(f"Error during create_multi_simulation: {e}", flush=True)
            for item in exprs:
                self.state.update_expression(item['expression'], 'PENDING')
            return None
            
        results = []
        if isinstance(res, dict):
            if res.get('error'):
                print(f"Error from platform API: {res.get('error')}", flush=True)
                for item in exprs:
                    self.state.update_expression(item['expression'], 'PENDING')
                return None
                
            alpha_results = res.get('alpha_results', [])
            for i, alpha_item in enumerate(alpha_results):
                alpha_data = alpha_item.get('details')
                alpha_id = alpha_item.get('alpha_id')
                
                if not isinstance(alpha_data, dict) and alpha_id:
                    print(f"Missing details for {alpha_id}, attempting to fetch manually...", flush=True)
                    # Attempt manual fetch with retry
                    for _ in range(3):
                        time.sleep(5)
                        detail_res = self.api.get_alpha(alpha_id)
                        if detail_res and detail_res.status_code == 200:
                            alpha_data = detail_res.json()
                            break
                    if not isinstance(alpha_data, dict):
                        print(f"Failed to manually fetch details for {alpha_id}.", flush=True)
                
                if not isinstance(alpha_data, dict):
                    print(f"Skipping result due to missing details. Error: {alpha_item.get('error')}", flush=True)
                    # If it's literally missing the alpha ID, it was a hard simulation failure
                    if alpha_item.get('error') == 'No alpha ID found in completed simulation':
                        # Try to map back to expression
                        expr_found = ''
                        if i < len(exprs):
                            expr_found = exprs[i]['expression']
                        if expr_found:
                            self.state.update_expression(expr_found, 'FAIL', metrics={'error': 'No alpha ID found'})
                    continue
                
                # Try to map back to expression
                expr_found = alpha_data.get('regular')
                if isinstance(expr_found, dict):
                    expr_found = expr_found.get('code', '')
                elif not isinstance(expr_found, str):
                    expr_found = alpha_data.get('expression', '')
                    if isinstance(expr_found, dict):
                        expr_found = expr_found.get('code', '')

                # Fallback to the original expression we sent in this chunk
                if not expr_found and i < len(exprs):
                    expr_found = exprs[i]['expression']

                alpha_id = alpha_item.get('alpha_id') or alpha_data.get('id')
                
                if alpha_id and expr_found:
                    # Also write back the settings so we can track it correctly
                    settings = exprs[i].get('settings', {}) if i < len(exprs) else {}
                    self.state.update_expression(expr_found, 'COMPLETE', alpha_id=alpha_id, metrics=alpha_data, settings=settings)
                    results.append({'expr': expr_found, 'alpha_id': alpha_id, 'details': alpha_data, 'settings': settings})
        return results

    def run_loop(self):
        batch_count = 0
        while True:
            # Dynamically reload alpha_generator so user can edit templates on the fly
            importlib.reload(alpha_generator)
            
            success_pool = self.state.get_success_pool()
            if len(success_pool) >= 10:
                print("Goal reached! 10 Alphas found.")
                generate_diversity_report(self.state, batch_count)
                break
                
            dataset_id = "targeted_opt"
            untested_fields = ["dummy"]  # just to pass any checks
            
            # Since we do targeted opt, we don't care about exhausting fields.
            # We just generate expressions and run them.
            exprs, selected_fields = alpha_generator.generate_expressions(dataset_id, untested_fields, max_fields=2)
            
            if not exprs:
                print("No expressions generated.")
                time.sleep(30)
                continue
                
            pending_exprs = []
            for item in exprs:
                # Add if not exists
                settings = item.get('settings', {})
                try:
                    self.state.add_expression(item['expression'], item['dataset_id'], item['field_id'], settings=settings)
                except sqlite3.IntegrityError:
                    pass
                
                # Check status
                status = self.state.get_expression_status(item['expression'], settings=settings)
                if status == "PENDING" or status is None:
                    pending_exprs.append(item)
                    
            if not pending_exprs:
                print("All generated expressions have already been tested. Retrying...")
                time.sleep(5)
                continue
                
            # Group pending expressions by their settings_override json string
            grouped_exprs = {}
            for item in pending_exprs:
                settings_key = json.dumps(item.get('settings', {}), sort_keys=True)
                grouped_exprs.setdefault(settings_key, []).append(item)

            chunk_size = 8
            for settings_key, group in grouped_exprs.items():
                settings_override = json.loads(settings_key)
                for i in range(0, len(group), chunk_size):
                    chunk = group[i:i+chunk_size]
                    
                    while True:
                        print(f"Batch {batch_count+1}: Testing {len(chunk)} expressions with settings {settings_key}", flush=True)
                        results = self.simulate_batch(chunk, settings_override=settings_override)
                        
                        if results is None:
                            print("simulate_batch failed. Re-authenticating and retrying in 60s...", flush=True)
                            try:
                                cred_path = r'D:\code\WorldQuant Brain\goal\Password\config.yaml'
                                cred = yaml.safe_load(open(cred_path, encoding='utf-8'))
                                asyncio.run(authenticate(cred['username'], cred['password']))
                            except Exception as e:
                                print(f"Re-auth failed: {e}", flush=True)
                            time.sleep(60)
                            continue
                        else:
                            break
                    
                    for r in results:
                        # Check metrics
                        passed, reason = evaluate_metrics(r['details'])
                        if not passed:
                            self.state.update_expression(r['expr'], 'FAIL', settings=r['settings'])
                            continue
                            
                        passed, reason = evaluate_neutralized(r['details'])
                        if not passed:
                            self.state.update_expression(r['expr'], 'FAIL', settings=r['settings'])
                            continue
                            
                        # Passed hard checks, now robust & PROD correlation
                        check_res = self.api.get_submission_check(r['alpha_id'])
                        if check_res and check_res.status_code == 200:
                            check_data = check_res.json()
                            is_submittable = check_data.get('isSubmittable', False)
                            if is_submittable:
                                self.state.update_expression(r['expr'], 'SUCCESS_POOL', alpha_id=r['alpha_id'], settings=r['settings'])
                                print(f"Found successful alpha! {r['alpha_id']}", flush=True)
                            else:
                                self.state.update_expression(r['expr'], 'FAIL_CHECK', settings=r['settings'])
                        else:
                            self.state.update_expression(r['expr'], 'PENDING', settings=r['settings'])
                            
                    batch_count += 1
                    if batch_count % 10 == 0:
                        generate_diversity_report(self.state, batch_count)
                        
                    # Increased delay to 30s to allow user to view/modify code between batches
                    print("Waiting 30s before next batch to allow manual script adjustments...", flush=True)
                    time.sleep(30)

if __name__ == "__main__":
    runner = MinerRunner()
    runner.run_loop()
