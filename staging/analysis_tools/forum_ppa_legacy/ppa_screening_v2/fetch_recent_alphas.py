import requests, yaml, datetime, json
cred = yaml.safe_load(open(r'D:\code\WorldQuant Brain\goal\Password\config.yaml', encoding='utf-8'))
s = requests.Session()
s.post('https://api.worldquantbrain.com/authentication', json=cred)
alphas = []
for offset in range(0, 1000, 100):
    res = s.get(f'https://api.worldquantbrain.com/users/self/alphas?limit=100&offset={offset}').json()
    batch = res.get('results', [])
    if not batch: break
    alphas.extend(batch)
seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
recent = []
for a in alphas:
    if not a.get('dateCreated'): continue
    dt = datetime.datetime.fromisoformat(a['dateCreated'].replace('Z', '+00:00'))
    if dt < seven_days_ago: continue
    # Extract region from settings
    region = a.get('settings', {}).get('region', '')
    if region != 'DEU': continue
    
    metrics = a.get('is', {}) or {}
    sharpe = metrics.get('sharpe', -1)
    if sharpe is not None and sharpe > 0.8:
        recent.append(a)
print(f'Found {len(recent)} matching alphas.')
for a in recent[:5]:
    expr = a.get('regular', {}).get('code', a.get('expression', ''))
    sharpe = (a.get('is', {}) or {}).get('sharpe')
    print(f"ID: {a['id']}, Sharpe: {sharpe}, Expr: {expr}")
with open('recent_deu_alphas.json', 'w') as f: json.dump(recent, f, indent=2)
