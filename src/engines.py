# src/engines.py
import csv
from pathlib import Path
from fontTools.ttLib import TTFont

def analyze_and_filter(fpath, min_glyph_threshold=5000):
    """深度解析並標記風險項目 (純邏輯層)"""
    data = {'Name': '', 'Count': 0, 'Lang': 'Other', 'License': 'Unknown', 
            'Risk_Tag': [], 'Size_MB': 0, 'Path': str(fpath)}
    
    data['Size_MB'] = round(fpath.stat().st_size / (1024*1024), 2)
    
    try:
        with TTFont(fpath, fontNumber=0, lazy=True) as font:
            names = font['name']
            # ... (這裡放你原本的解析邏輯) ...
            # 判斷版權、字數、語系等
            # 將原本的 data['Risk_Tag'].append(...) 邏輯移到這裡
            pass 
    except Exception:
        data['Name'] = "無法讀取"
        data['Risk_Tag'].append("❌ 損毀")
        
    data['Risk_Tag'] = " | ".join(data['Risk_Tag']) if data['Risk_Tag'] else "✅ 安全"
    return data
