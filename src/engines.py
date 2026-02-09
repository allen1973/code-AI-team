from pathlib import Path
import hashlib
from fontTools.ttLib import TTFont

def analyze_and_filter(fpath: Path, min_glyph_threshold: int = 5000):
    """
    深度解析字體檔案並標記風險項目。
    
    Args:
        fpath (Path): 字體檔案的 pathlib.Path 對象
        min_glyph_threshold (int): 判定為「字數過少」的門檻
        
    Returns:
        dict: 包含字體名稱、風險標籤、語系、字數等資訊的字典
    """
    data = {
        'Name': '', 
        'Risk_Tag': [], 
        'Lang': 'Other', 
        'Count': 0, 
        'License': 'Unknown', 
        'Size_MB': 0, 
        'Path': str(fpath)
    }
    
    # 1. 計算基礎檔案資訊
    try:
        data['Size_MB'] = round(fpath.stat().st_size / (1024 * 1024), 2)
    except Exception:
        data['Risk_Tag'].append("⚠️ 無法讀取檔案大小")

    # 2. 解析字體內部資訊
    try:
        with TTFont(fpath, fontNumber=0, lazy=True) as font:
            # 取得字體名稱與版權資訊
            names = font['name']
            
            # 名稱 (ID 4: Full Name)
            name_rec = names.getName(4, 3, 1, 1033) or names.getName(4, 3, 1, 1028)
            data['Name'] = name_rec.toUnicode() if name_rec else fpath.stem
            
            # 授權資訊 (ID 13: License Description)
            lic_rec = names.getName(13, 3, 1, 1033) or names.getName(14, 3, 1, 1033)
            lic_text = lic_rec.toUnicode().lower() if lic_rec else ""
            
            # 判斷授權風險
            if any(k in lic_text for k in ['open font', 'sil', 'apache', 'ofl', 'free', 'public domain']):
                data['License'] = "Open Source"
            elif any(k in lic_text for k in ['commercial', 'licensed', 'all rights reserved', 'proprietary']):
                data['License'] = "Commercial"
                data['Risk_Tag'].append("💰 商用注意")
            else:
                data['License'] = "Unknown"
                data['Risk_Tag'].append("❓ 授權不明")

            # 3. 字數與語系判定
            cmap = font.getBestCmap()
            if cmap:
                chars = list(cmap.keys())
                data['Count'] = len(chars)
                
                # 判定繁簡中文字 (基於 Unicode 區段)
                is_tc = any(c in chars for c in [0x4E00, 0x863F]) # 基礎中文字
                is_sc = any(c in chars for c in [0x4E0E, 0x8FDE]) # 簡體特有字
                
                if is_tc and is_sc: data['Lang'] = "中日韓 (繁簡全)"
                elif is_tc: data['Lang'] = "繁體中文"
                elif is_sc: data['Lang'] = "簡體中文"
                else: data['Lang'] = "西文/其他"

                # 判定缺字風險
                if data['Count'] < min_glyph_threshold:
                    data['Risk_Tag'].append("⚠️ 字數過少")

    except Exception as e:
        data['Name'] = fpath.stem
        data['Risk_Tag'].append(f"❌ 損毀或無法解析: {str(e)}")
        
    # 格式化 Risk_Tag 為字串
    data['Risk_Tag'] = " | ".join(data['Risk_Tag']) if data['Risk_Tag'] else "✅ 安全"
    return data
