import os
import zlib
import json
import pandas as pd
import msgpack
import glob

def convert_bytes(obj):
    if isinstance(obj, bytes):
        return obj.decode('utf-8', 'ignore')
    elif isinstance(obj, dict):
        return {convert_bytes(k): convert_bytes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_bytes(v) for v in obj]
    return obj

def load_wds_bin(filepath):
    """
    Reads a WebDataScope .bin file, decompresses zlib, unpacks MessagePack, 
    and returns a summarized Pandas DataFrame of field statistics.
    """
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} does not exist.")
        return pd.DataFrame()
        
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
            decompressed = zlib.decompress(data)
            parsed = msgpack.unpackb(decompressed, raw=False)
            
        parsed = convert_bytes(parsed)
        
        field_stats = []
        for field_name, stats in parsed.items():
            if not isinstance(stats, dict) or 'CoverageRatio' not in stats:
                continue
                
            coverage_arr = stats.get('CoverageRatio', [])
            skewness_arr = stats.get('skenewss', [])
            kurtosis_arr = stats.get('kurtosis', [])
            positive_vals = stats.get('PositiveValues', [])
            negative_vals = stats.get('NegativeValues', [])
            int_status_arr = stats.get('IntegerStatus', [])
            abs_ratio_arr = stats.get('absValueBetween1and0ratio', [])
            
            # 过滤掉缺失年份（如果有的话，通常数组长度代表年数）
            avg_coverage = sum(coverage_arr) / len(coverage_arr) if coverage_arr else 0
            min_coverage = min(coverage_arr) if coverage_arr else 0
            max_coverage = max(coverage_arr) if coverage_arr else 0
            
            avg_skewness = sum(skewness_arr) / len(skewness_arr) if skewness_arr else 0
            avg_kurtosis = sum(kurtosis_arr) / len(kurtosis_arr) if kurtosis_arr else 0
            avg_abs_ratio = sum(abs_ratio_arr) / len(abs_ratio_arr) if abs_ratio_arr else 0
            is_integer = int_status_arr[-1] == 1 if int_status_arr else False # 取最后一年状态
            
            total_positive = sum(positive_vals) if positive_vals else 0
            total_negative = sum(abs(n) for n in negative_vals) if negative_vals else 0
            
            pos_ratio = total_positive / (total_positive + total_negative) if (total_positive + total_negative) > 0 else 0
            
            field_stats.append({
                'Field': field_name,
                'AvgCoverage': round(avg_coverage, 3),
                'MinCoverage': round(min_coverage, 3),
                'MaxCoverage': round(max_coverage, 3),
                'AvgSkewness': round(avg_skewness, 3),
                'AvgKurtosis': round(avg_kurtosis, 3),
                'PositiveRatio': round(pos_ratio, 3),
                'AbsRatio(0~1)': round(avg_abs_ratio, 3),
                'IsInteger': is_integer,
                'Frequency': stats.get('frequency', [''])[0] if isinstance(stats.get('frequency'), list) and stats.get('frequency') else 'unknown',
                'CoverageTrend': coverage_arr
            })
            
        df = pd.DataFrame(field_stats)
        if len(df) > 0:
            df = df.sort_values(by='AvgCoverage', ascending=False).reset_index(drop=True)
        return df
        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return pd.DataFrame()

def list_available_datasets(data_dir):
    """
    Returns a list of all dataset names available in the data directory.
    """
    pattern = os.path.join(data_dir, '*.bin')
    files = glob.glob(pattern)
    datasets = [os.path.basename(f).replace('.bin', '') for f in files]
    return sorted(datasets)

if __name__ == "__main__":
    # Test execution
    test_file = r"d:\code\WorldQuant Brain\goal\WebDataScope-0.10.11\data\analyst47_GLB_TOP3000_Delay1.bin"
    df = load_wds_bin(test_file)
    print(df.head())
