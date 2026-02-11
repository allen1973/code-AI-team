# -*- coding: utf-8 -*-
"""
FontAuditor_Mac_V3.py
修正版：解決 fontTools 版本相容性問題
"""

import os
import csv
import re
import hashlib
import gc
from pathlib import Path
from datetime import datetime

def install_requirements():
    try:
        from fontTools.ttLib import TTFont
        from tqdm import tqdm
    except ImportError:
        print("正在安裝或更新必要套件 (fonttools, tqdm)...")
        os.system('pip3 install --upgrade fonttools tqdm -q')

install_requirements()
from fontTools.ttLib import TTFont
from tqdm import tqdm

def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return "MD5_Error"

def get_clean_meta(name_table, name_id):
    # 嘗試不同編碼紀錄 (ID4: Full Name, ID1: Family Name)
    record = name_table.getName(name_id, 3, 1, 1033) or \
             name_table.getName(name_id, 1, 0, 0) or \
             name_table.getName(name_id, 3, 1, 1028)
    if not record: return "N/A"
    try:
        return re.sub(r'\s+', ' ', record.toUnicode()).strip()
    except:
        return "Encoding Error"

def run_audit():
    print("=== macOS 字體深度盤點工具 V3 (相容性修正版) ===")
    
    default_scan = "/Library/Fonts"
    user_input = input(f"👉 掃描路徑 (預設 {default_scan}): ").strip()
    scan_root = user_input if user_input else default_scan
    
    scan_path = Path(scan_root)
    if not scan_path.exists():
        print(f"❌ 錯誤: 找不到路徑 '{scan_root}'")
        return

    report_folder = Path.home() / "Desktop/Font_Audit_Reports"
    report_folder.mkdir(parents=True, exist_ok=True)
    csv_file = report_folder / f"Font_Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    fieldnames = ['狀態 (Status)', 'MD5_Hash', '字體全名 (ID4)', '字體家族 (ID1)', '版本 (ID5)', '檔案大小(MB)', '原始路徑', '衝突來源']
    font_exts = {'.ttf', '.otf', '.ttc', '.dfont'}
    
    print("🔍 正在檢索檔案結構...")
    file_list = []
    for p in scan_path.rglob('*'):
        try:
            if p.is_file() and p.suffix.lower() in font_exts and not p.name.startswith('._'):
                file_list.append(p)
        except:
            continue

    total_files = len(file_list)
    if total_files == 0:
        print("📭 找不到字體檔案。")
        return

    seen_hashes = {}
    duplicate_count = 0
    error_count = 0

    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        with tqdm(total=total_files, desc="盤點進度", unit="file", colour='green') as pbar:
            for file_path in file_list:
                font = None
                try:
                    # 第一階段：計算 MD5 (這部分你之前的結果顯示是成功的)
                    file_hash = get_file_md5(file_path)
                    
                    status = "Unique"
                    conflict_source = ""
                    if file_hash in seen_hashes:
                        status = "Duplicate"
                        conflict_source = seen_hashes[file_hash]
                        duplicate_count += 1
                    else:
                        seen_hashes[file_hash] = str(file_path)

                    # 第二階段：讀取 Metadata (已移除相容性問題參數)
                    # 只保留最基本的參數以確保舊版 fontTools 也能跑
                    font = TTFont(str(file_path), fontNumber=0, lazy=True)
                    names = font['name']

                    writer.writerow({
                        '狀態 (Status)': status,
                        'MD5_Hash': file_hash,
                        '字體全名 (ID4)': get_clean_meta(names, 4),
                        '字體家族 (ID1)': get_clean_meta(names, 1),
                        '版本 (ID5)': get_clean_meta(names, 5),
                        '檔案大小(MB)': round(file_path.stat().st_size / (1024 * 1024), 2),
                        '原始路徑': str(file_path),
                        '衝突來源': conflict_source
                    })
                except Exception as e:
                    error_count += 1
                    writer.writerow({
                        '狀態 (Status)': 'Read_Error',
                        'MD5_Hash': file_hash if 'file_hash' in locals() else 'N/A',
                        '字體全名 (ID4)': f"讀取失敗: {str(e)}",
                        '原始路徑': str(file_path)
                    })
                finally:
                    if font: font.close()
                    pbar.update(1)
                    if pbar.n % 50 == 0:
                        f.flush()
                        gc.collect()

    print("-" * 50)
    print(f"✨ 盤點完成！")
    print(f"📊 總處理數: {total_files}")
    print(f"⚠️ 重複數: {duplicate_count} | ❌ 讀取失敗數: {error_count}")
    print(f"🔗 報告路徑：{csv_file}")

if __name__ == "__main__":
    run_audit()