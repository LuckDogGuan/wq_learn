import requests
import yaml
import time
from .config import CREDENTIALS_PATH, API_BASE

class BrainAPI:
    def __init__(self):
        self.session = requests.Session()
        self.username = None
        self.password = None
        self._load_credentials()
        self.authenticate()

    def _load_credentials(self):
        with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
            cred = yaml.safe_load(f)
            self.username = cred['username']
            self.password = cred['password']

    def authenticate(self):
        auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        while True:
            try:
                res = self.session.post(f"{API_BASE}/authentication", auth=auth)
                if res.status_code == 201:
                    print("Authenticated successfully.")
                    break
                else:
                    print(f"Auth failed: {res.status_code}. Retrying in 10s...")
            except requests.RequestException as e:
                print(f"Network error during auth: {e}. Retrying in 10s...")
            time.sleep(10)

    def request_with_retry(self, method, endpoint, **kwargs):
        url = f"{API_BASE}{endpoint}"
        for attempt in range(6):
            try:
                if method.upper() == 'GET':
                    res = self.session.get(url, **kwargs)
                elif method.upper() == 'POST':
                    res = self.session.post(url, **kwargs)
                else:
                    raise ValueError("Unsupported method")
                
                if res.status_code in (401, 403):
                    print("Token expired or unauthorized, re-authenticating...")
                    self.authenticate()
                    continue
                elif res.status_code == 429:
                    print("429 Too Many Requests. Sleeping for 30s...")
                    time.sleep(30)
                    continue
                elif res.status_code >= 500:
                    print(f"5xx Server error ({res.status_code}). Retrying in 10s...")
                    time.sleep(10)
                    continue
                
                return res
            except requests.RequestException as e:
                print(f"Network error: {e}. Retrying in 10s...")
                time.sleep(10)
        return None  # Max retries exceeded

    def simulate(self, payload):
        return self.request_with_retry('POST', '/simulations', json=payload)

    def get_simulation_status(self, sim_id):
        return self.request_with_retry('GET', f'/simulations/{sim_id}')

    def get_alpha(self, alpha_id):
        return self.request_with_retry('GET', f'/alphas/{alpha_id}')

    def get_submission_check(self, alpha_id):
        return self.request_with_retry('GET', f'/alphas/{alpha_id}/check')
        
    def get_alpha_correlation(self, alpha_id):
        return self.request_with_retry('GET', f'/alphas/{alpha_id}/correlations')
        
    def get_datasets(self):
        res = self.request_with_retry('GET', '/data-sets?instrumentType=EQUITY&region=DEU&delay=1')
        if res and res.status_code == 200:
            return [d['id'] for d in res.json().get('results', [])]
        return []
        
    def get_datafields(self, dataset_id):
        res = self.request_with_retry('GET', f'/data-fields?dataset.id={dataset_id}&region=DEU&delay=1&limit=50')
        if res and res.status_code == 200:
            return [d['id'] for d in res.json().get('results', [])]
        return []
