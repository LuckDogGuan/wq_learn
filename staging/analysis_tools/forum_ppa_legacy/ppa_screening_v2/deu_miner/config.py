import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATEFIELDS_CSV = os.path.join(BASE_DIR, 'DateFields', 'datafields_DEU_1_TOP500.csv')
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'Password', 'config.yaml')
DB_PATH = os.path.join(os.path.dirname(__file__), 'deu_miner_state.db')
REPORT_DIR = os.path.join(BASE_DIR, '总结')
os.makedirs(REPORT_DIR, exist_ok=True)
REPORT_PATH = os.path.join(REPORT_DIR, 'deu_datefields_diversity.md')

SETTINGS = {
    'instrumentType': 'EQUITY',
    'region': 'DEU',
    'universe': 'TOP500',  # We can change this later to TOP1200 or others for DEU
    'delay': 1,
    'decay': 0,
    'neutralization': 'SUBINDUSTRY',
    'truncation': 0.08,
    'pasteurization': 'ON',
    'unitHandling': 'VERIFY',
    'nanHandling': 'OFF',
    'language': 'FASTEXPR',
    'visualization': False,
}

HARD_THRESHOLDS = {
    'is_sharpe': 1.58,
    'is_fitness': 1.0,
    'is_2y_sharpe': 1.6,
    'margin_bp': 10,
    'turnover_min': 0.05,
    'turnover_max': 0.30,
    'neut_sharpe': 1.0,
    'neut_fitness': 0.7,
    'neut_margin_bp': 10,
    'max_operators': 5
}

API_BASE = 'https://api.worldquantbrain.com'
