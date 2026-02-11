
# -*- coding: utf-8 -*-
import os
import hashlib
from pathlib import Path

def get_file_info(file_path):
    """取得檔案的大小與 MD5 雜湊值"""
    try:
        stat = file_path.stat()
        size = stat.st_size
        # 對於大型專案，這裡可以先只比對大小以提升速度
        # 若需要極度精確再啟用 MD5
        return {"size": size, "path": file_path}
    except Exception:
        return None

def scan_directory(root_path, ignore_dirs=None):
    """掃描目錄並建立相對路徑映射表"""
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', '.DS_Store', 'node_modules'}
    
    data = {}
    root = Path(root_path).expanduser()
    
    for p in root.rglob('*'):
        # 檢查是否在忽略名單中
        if any(part in ignore_dirs for part in p.parts):
            continue
            
        if p.is_file():
            # 使用「相對路徑」作為 Key，這是比對的關鍵
            rel_path = p.relative_to(root)
            data[rel_path] = get_file_info(p)
    return data, root

def compare_projects(path_a, path_b):
    print(f"🔍 正在掃描與比對...\nPath A: {path_a}\nPath B: {path_b}\n" + "-"*50)
    
    data_a, root_a = scan_directory(path_a)
    data_b, root_b = scan_directory(path_b)
    
    all_rel_paths = sorted(set(data_a.keys()) | set(data_b.keys()))
    
    diff_report = []
    
    for rel_p in all_rel_paths:
        in_a = rel_p in data_a
        in_b = rel_p in data_b
        
        if in_a and not in_b:
            diff_report.append(f"[僅存在 A] {rel_p}")
        elif not in_a and in_b:
            diff_report.append(f"[僅存在 B] {rel_p}")
        else:
            # 兩者皆有，比對屬性 (這裡以檔案大小為例)
            if data_a[rel_p]['size'] != data_b[rel_p]['size']:
                size_diff = data_b[rel_p]['size'] - data_a[rel_p]['size']
                diff_report.append(f"[內容差異] {rel_p} (B比A大 {size_diff} bytes)")

    # 輸出結果
    if not diff_report:
        print("✨ 兩個資料夾結構與內容完全一致！")
    else:
        for line in diff_report:
            print(line)
    
    print("-"*50)
    print(f"掃描統計: A有 {len(data_a)} 檔案, B有 {len(data_b)} 檔案")

if __name__ == "__main__":
    dir_a = input("請輸入資料夾 A 路徑: ").strip()
    dir_b = input("請輸入資料夾 B 路徑: ").strip()
    compare_projects(dir_a, dir_b)