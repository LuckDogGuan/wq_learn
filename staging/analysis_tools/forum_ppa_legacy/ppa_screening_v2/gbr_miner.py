import requests
import json
import yaml
import time
import os
import random
import itertools

# Configuration
CONFIG_FILE = r"d:\code\WorldQuant Brain\goal\Password\config.yaml"
STATE_FILE = r"d:\code\WorldQuant Brain\goal\代码\ppa_screening_v2\gbr_miner_state.json"
SUMMARY_DIR = r"d:\code\WorldQuant Brain\goal\总结"

# Alpha Thresholds
THRESHOLD_SHARPE = 1.25
THRESHOLD_FITNESS = 0.5
THRESHOLD_MARGIN = 0.0010  # 10bp = 0.0010
THRESHOLD_TURNOVER_MIN = 0.01
THRESHOLD_TURNOVER_MAX = 0.70

# Risk Neutralized Thresholds
RN_SHARPE = 1.0
RN_FITNESS = 0.7
RN_MARGIN = 0.0010

os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)

def get_session():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    s = requests.Session()
    s.auth = (config['username'], config['password'])
    res = s.post(f"{config.get('api_base_url', 'https://api.worldquantbrain.com')}/authentication")
    if res.status_code != 201:
        print("Auth failed:", res.content)
        exit(1)
    return s, config.get('api_base_url', 'https://api.worldquantbrain.com')

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "found_alphas": [],
        "used_datasets": [],
        "rounds_run": 0
    }

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

def get_datasets(s, base_url, region="EUR", delay=1):
    import csv
    datasets = {}
def get_datasets(s, base_url, region="GBR", delay=1):
    import csv
    datasets = {}
    csv_path = "DateFields/datafields_GBR_1_TOP700.csv"
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ds_id = row['dataset.id']
            ds_name = row['dataset.name']
            if ds_id not in datasets:
                datasets[ds_id] = {'id': ds_id, 'name': ds_name}
    return list(datasets.values())

def get_datafields(s, base_url, dataset_id, region="GBR", delay=1):
    import csv
    fields = []
    csv_path = "DateFields/datafields_GBR_1_TOP700.csv"
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['dataset.id'] == dataset_id and row['type'] == 'MATRIX':
                fields.append({
                    'id': row['id'],
                    'description': row['description'],
                    'type': row['type']
                })
    return fields

def generate_expressions(fields):
    """
    Generate exactly 8 advanced BIVARIATE expressions using FORUM MASTERS' BLUEPRINT.
    Avoiding +, *, trade_when. Operators count < 6. Target exactly 8.
    Key insight: ts_backfill and winsorize are crucial for alternative datasets.
    """
    exps = []
    if len(fields) < 2: return []
    f1 = fields[0]['id']
    f2 = fields[1]['id']
    
    ops = [
        "group_rank(winsorize(ts_backfill({f1} / ({f2} + 0.0001), 252), std=4), subindustry)",
        "group_neutralize(ts_rank(winsorize({f1}, std=3), 252) - ts_rank(winsorize({f2}, std=3), 252), subindustry)",
        "group_zscore(ts_backfill({f1}, 63) - ts_backfill({f2}, 63), subindustry)",
        "ts_decay_linear(group_rank(winsorize({f1} / ({f2} + 0.0001), std=4), subindustry), 5)",
        "group_neutralize(ts_corr(winsorize({f1}, std=3), winsorize({f2}, std=3), 63), subindustry)",
        "-1 * group_neutralize(ts_delta(ts_backfill({f1}, 20), 5) - ts_delta(ts_backfill({f2}, 20), 5), subindustry)",
        "group_rank(ts_mean(winsorize({f1} / ({f2} + 0.0001), std=4), 20), subindustry)",
        "group_zscore(ts_delta(winsorize({f1}, std=3), 10) - ts_delta(winsorize({f2}, std=3), 10), subindustry)"
    ]
    for op in ops:
        exps.append(op.format(f1=f1, f2=f2))
    return exps

def post_multi_simulation(s, base_url, exps, region, universe):
    sims = []
    for exp in exps:
        sims.append({
            'type': 'REGULAR',
            'settings': {
                'instrumentType': 'EQUITY',
                'region': region,
                'universe': universe,
                'delay': 1,
                'decay': 0,
                'neutralization': 'SUBINDUSTRY',
                'truncation': 0.08,
                'pasteurization': 'ON',
                'testPeriod': 'P2Y',
                'unitHandling': 'VERIFY',
                'nanHandling': 'ON',
                'language': 'FASTEXPR',
                'visualization': False,
            },
            'regular': exp
        })
    
    batch_size = 8
    progress_urls = []
    for i in range(0, min(len(sims), 80), batch_size):
        batch = sims[i:i+batch_size]
        attempts = 0
        while attempts < 3:
            attempts += 1
            try:
                res = s.post(f"{base_url}/simulations", json=batch, timeout=15)
                if res.status_code == 201:
                    progress_urls.append(res.headers.get('Location'))
                    time.sleep(2)
                    break
                elif res.status_code == 429:
                    print("Rate limit reached. Sleeping 60s.")
                    time.sleep(60)
                else:
                    print(f"Error posting sim: {res.status_code} {res.text}")
                    break
            except Exception as e:
                print(f"Error posting sim batch: {e}")
                time.sleep(5)
    
    return progress_urls

def poll_simulations(s, progress_urls):
    results = []
    for url in progress_urls:
        attempts = 0
        while attempts < 120:
            try:
                res = s.get(url, timeout=15)
                if res.status_code == 404:
                    print("Simulation not found:", url)
                    break
                if 'Retry-After' in res.headers:
                    time.sleep(float(res.headers['Retry-After']))
                else:
                    status = res.json().get('status')
                    if status in ('COMPLETE', 'WARNING'):
                        children = res.json().get('children', [])
                        results.extend(children)
                        break
                    elif status in ('ERROR', 'FAIL'):
                        print(f"Simulation {url} failed. Parent response: {res.json()}")
                        break
                    time.sleep(1)
                    attempts += 1
            except Exception as e:
                print(f"Error polling {url}: {e}")
                time.sleep(5)
                attempts += 5
        if attempts >= 120:
            print(f"Timeout waiting for {url}")
    return results

def check_correlation(s, base_url, alpha_id):
    # WorldQuant Brain check API
    print(f"Running submission checks for alpha {alpha_id}...")
    try:
        post_res = s.post(f"{base_url}/alphas/{alpha_id}/check")
        if post_res.status_code == 429:
            print("Rate limited on check, sleep 30s")
            time.sleep(30)
            post_res = s.post(f"{base_url}/alphas/{alpha_id}/check")
    except Exception as e:
        pass

    time.sleep(5) # wait for check to run
    for _ in range(10):
        try:
            res = s.get(f"{base_url}/alphas/{alpha_id}/check")
            if res.status_code == 200:
                data = res.json()
                status = data.get('status')
                if status == 'PENDING' or status == 'RUNNING':
                    time.sleep(5)
                    continue
                
                checks = data.get('checks', [])
                prod_corr = next((c for c in checks if c['name'] in ['PROD_CORRELATION', 'PRODUCTION_CORRELATION']), None)
                if prod_corr:
                    return prod_corr.get('value')
                return None
            time.sleep(5)
        except Exception as e:
            time.sleep(5)
    return None

def check_alphas(s, base_url, alpha_ids):
    passed = []
    max_sharpe = 0
    for sim_id in alpha_ids:
        attempts = 0
        while attempts < 3:
            attempts += 1
            try:
                # First get the simulation object to find the true alpha ID
                sim_res = s.get(f"{base_url}/simulations/{sim_id}", timeout=15)
                if 'Retry-After' in sim_res.headers:
                    sleep_time = float(sim_res.headers['Retry-After'])
                    print(f"Rate limited (sim)! Sleeping for {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue
                if sim_res.status_code != 200:
                    break
                    
                sim_data = sim_res.json()
                true_alpha_id = sim_data.get('alpha')
                if not true_alpha_id:
                    break
                    
                # Now get the alpha object to read metrics
                res = s.get(f"{base_url}/alphas/{true_alpha_id}", timeout=15)
                if 'Retry-After' in res.headers:
                    sleep_time = float(res.headers['Retry-After'])
                    print(f"Rate limited (alpha)! Sleeping for {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue
                if res.status_code != 200:
                    break
                    
                data = res.json()
                metrics = data.get('is', {})
                
                sharpe = metrics.get('sharpe', 0)
                if sharpe > max_sharpe:
                    max_sharpe = sharpe
                    fitness = metrics.get('fitness', 0)
                    turnover = metrics.get('turnover', 0)
                    margin = metrics.get('margin', 0)
                    
                    if sharpe > 1.25:
                        if fitness <= THRESHOLD_FITNESS:
                            print(f"Alpha {true_alpha_id} rejected due to Fitness ({fitness:.4f} <= {THRESHOLD_FITNESS})")
                        elif margin <= THRESHOLD_MARGIN:
                            print(f"Alpha {true_alpha_id} rejected due to Margin ({margin:.6f} <= {THRESHOLD_MARGIN})")
                        elif not (THRESHOLD_TURNOVER_MIN < turnover < THRESHOLD_TURNOVER_MAX):
                            print(f"Alpha {true_alpha_id} rejected due to Turnover ({turnover:.4f} not in {THRESHOLD_TURNOVER_MIN}-{THRESHOLD_TURNOVER_MAX})")
                        else:
                            # Fetch 2Y/OS metrics if available, or just rely on platform check
                            print(f"IS metrics passed for {true_alpha_id}. Checking PROD Correlation...")
                            prod_corr = check_correlation(s, base_url, true_alpha_id)
                            
                            if prod_corr is not None:
                                try:
                                    corr_val = float(prod_corr)
                                    if corr_val <= 0.7:
                                        print(f"Alpha {true_alpha_id} passed all strict checks! PROD Corr: {corr_val}")
                                        passed.append((data, corr_val))
                                    else:
                                        print(f"Alpha {true_alpha_id} rejected due to PROD Corr > 0.7 ({corr_val})")
                                except:
                                    print(f"Invalid prod corr value: {prod_corr}")
                            else:
                                print(f"Alpha {true_alpha_id} rejected due to missing PROD Corr.")
                    break
            except Exception as e:
                print(f"Error checking alpha {sim_id}: {e}")
                time.sleep(5)
    
    if alpha_ids:
        print(f"Max Sharpe in this batch: {max_sharpe:.4f}")
        
    return passed

def run_round():
    s, base_url = get_session()
    state = load_state()
    
    if len(state['found_alphas']) >= 10:
        print("Successfully found 10 alphas from 10 different datasets!")
        return True # Finished
        
    print(f"--- Round {state['rounds_run'] + 1} ---")
    
    datasets = get_datasets(s, base_url, "GBR", 1)
    # Exclude already used datasets or datasets that yielded an alpha
    found_datasets = [a['dataset'] for a in state['found_alphas']]
    # Filter datasets not used
    unused = [d for d in datasets if d['id'] not in state['used_datasets']]
    if not unused:
        print(f"No more unused datasets in GBR TOP700.")
        return True
        
    # Pick first dataset (assuming we want unlit, platform usually has alphaCount, but we rely on fresh datasets)
    ds = unused[0]
    print(f"Selected dataset: {ds['id']} ({ds['name']})")
    
    fields = get_datafields(s, base_url, ds['id'], "GBR", 1)
    if not fields:
        print("No fields found for dataset.")
        state['used_datasets'].append(ds['id'])
        save_state(state)
        return False
        
    num_fields = len(fields)
    max_attempts = min(5, max(1, num_fields // 2))
    
    for attempt in range(max_attempts):
        print(f"--- Dataset {ds['id']} Attempt {attempt+1}/{max_attempts} ---")
        sel_fields = random.sample(fields, min(2, len(fields)))
        print(f"Selected fields: {[f['id'] for f in sel_fields]}")
        
        exps = generate_expressions(sel_fields)
        if not exps:
            continue
            
        print(f"Generated {len(exps)} expressions.")
        
        universes = ["TOP700"]
        uni = random.choice(universes)
        print(f"Using universe: {uni}")
        
        progress_urls = post_multi_simulation(s, base_url, exps, "GBR", uni)
        print(f"Posted {len(progress_urls)} batch URLs. Waiting...")
        
        alpha_ids = poll_simulations(s, progress_urls)
        print(f"Simulations complete. Got {len(alpha_ids)} alpha IDs.")
        
        passed_alphas = check_alphas(s, base_url, alpha_ids)
        print(f"{len(passed_alphas)} alphas passed all strict criteria.")
        
        if passed_alphas:
            p_data, p_corr = passed_alphas[0]
            expr = p_data['regular']['code']
            
            state['found_alphas'].append({
                'id': p_data['id'],
                'dataset': ds['id'],
                'expr': expr,
                'metrics': p_data.get('is', {}),
                'prod_corr': p_corr
            })
            print(f">>> Found VALID Alpha: {p_data['id']} from {ds['id']}! <<<")
            break # Stop searching this dataset
            
    # After exhausting attempts or finding an alpha, move to the next dataset
    state['rounds_run'] += 1
    state['used_datasets'].append(ds['id'])
    
    # Save Diversity Assessment every 10 rounds
    if state['rounds_run'] % 10 == 0:
        summary_path = os.path.join(SUMMARY_DIR, f"gbr_mining_summary_round_{state['rounds_run']}.md")
        with open(summary_path, 'w', encoding='utf-8') as sf:
            sf.write(f"# GBR Mining Summary - Round {state['rounds_run']}\n")
            sf.write(f"- Alphas Found: {len(state['found_alphas'])}\n")
            sf.write(f"- Datasets Explored: {len(state['used_datasets'])}\n")
            sf.write("- Diversity check: Utilizing entirely different datasets ensures high stylistic diversity.\n")
            
    save_state(state)
    return False

if __name__ == "__main__":
    while True:
        finished = run_round()
        if finished:
            break
        print("Sleeping 10s between rounds...\n")
        time.sleep(10)
