import json
import glob

for f in glob.glob(r'C:\Users\31186\.gemini\antigravity\brain\64f3a19e-6d98-40e0-9629-0f3c78078de4\.system_generated\steps\605*\output.txt'):
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        if data.get('count', 0) > 0:
            dataset = data['results'][0]['dataset']['id']
            print(f"\nDataset: {dataset}")
            for r in data['results'][:15]:  # limit to 15 to avoid massive output
                print(f"{r['id']}: {r['description']}")
