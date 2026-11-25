import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    rec_path = 'exports/region_recommendations_updated.json'
    if not os.path.exists(rec_path):
        print(f"Error: Could not find {rec_path}")
        return
        
    with open(rec_path, 'r', encoding='utf-8') as f:
        rec_data = json.load(f)

    regions = list(rec_data.keys())
    script_path = 'generate_wds_ipynb.py'
    
    # Set env var for subprocess encoding
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    for region in regions:
        print(f"\n{'='*50}")
        print(f"Processing Region: {region}")
        print(f"{'='*50}\n")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content = re.sub(r'TARGET_REGION\s*=\s*".*?"', f'TARGET_REGION = "{region}"', content)
        content = re.sub(r'TARGET_THEME\s*=\s*".*?"', f'TARGET_THEME = "None"', content)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"-> Generating notebook for {region}...")
        res_gen = subprocess.run(["python", script_path], capture_output=True, env=env)
        if res_gen.returncode != 0:
            print("Error generating notebook:", res_gen.stderr.decode('utf-8', errors='ignore'))
            continue
            
        print(f"-> Executing notebook to generate exports for {region}...")
        res_exec = subprocess.run(
            ["python", "-m", "jupyter", "nbconvert", "--execute", "--to", "notebook", "--inplace", "dataset_field_analysis.ipynb"], 
            capture_output=True, env=env
        )
        if res_exec.returncode != 0:
            print("Error executing notebook:", res_exec.stderr.decode('utf-8', errors='ignore'))
        else:
            print(f"Successfully processed {region}!")

    print("\nAll regions processed! Check the 'exports' folder.")

if __name__ == "__main__":
    main()
