import sys
import json
from pathlib import Path

# Add the directory containing the Core package, not Core itself.
project_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_dir))

from Core.api import login, get_user_diversity

data = get_user_diversity(login())
print("最终结果：")
print(json.dumps(data, ensure_ascii=False, indent=2))
