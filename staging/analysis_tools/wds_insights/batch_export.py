import json
import os
import shutil
import subprocess

# Read regions
regions_file = r'exports/region_recommendations_updated.json'
with open(regions_file, 'r', encoding='utf-8') as f:
    recommendations = json.load(f)

regions = list(recommendations.keys())

for region in regions:
    print(f"\\n{'='*50}")
    print(f"Processing Region: {region}")
    print(f"{'='*50}")
    
    # Update generate_wds_ipynb.py
    with open('generate_wds_ipynb.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    content = re.sub(
        r'TARGET_REGION\s*=\s*".*?"',
        f'TARGET_REGION = "{region}"',
        content
    )
    
    with open('generate_wds_ipynb.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    # Generate the notebook
    subprocess.run(['python', 'generate_wds_ipynb.py'], check=True)
    
    # Execute the notebook
    subprocess.run(['python', '-m', 'jupyter', 'nbconvert', '--execute', '--to', 'notebook', '--inplace', 'dataset_field_analysis.ipynb'], check=True)
    
    # Move files to a dedicated region folder
    region_dir = f'exports/{region}'
    os.makedirs(region_dir, exist_ok=True)
    
    # Move newly created txt and xlsx files
    for file in os.listdir('exports'):
        if file.endswith('.txt') or file.endswith('.xlsx'):
            if f'_{region}_' in file:
                src = os.path.join('exports', file)
                dst = os.path.join(region_dir, file)
                # Overwrite if exists
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(src, dst)
    print(f"✅ Region {region} completed!")

# Handle Plugin data
plugin_file = 'exports/Plugin_Neutralization_Insights.json'
if os.path.exists(plugin_file):
    os.makedirs('exports/Plugins_and_Rules', exist_ok=True)
    dst = 'exports/Plugins_and_Rules/Plugin_Neutralization_Insights.json'
    if os.path.exists(dst):
        os.remove(dst)
    shutil.move(plugin_file, dst)
print("✅ Batch export fully completed!")
