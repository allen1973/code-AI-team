# -*- coding: utf-8 -*-
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict

# ----------------環境設定----------------
IGNORE_LIST = {'.git', '__pycache__', '.DS_Store', 'node_modules', 'venv', '.idea'}

def get_file_hash(file_path):
    """計算檔案 MD5，增加緩衝區提升大檔案效率"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def scan_dir(path):
    """掃描目錄並回傳相對路徑映射表"""
    root = Path(path).expanduser()
    files_data = {}
    # 使用 tqdm 顯示掃描進度
    all_files = [p for p in root.rglob('*') if p.is_file() and not any(part in IGNORE_LIST for part in p.parts)]
    
    for p in tqdm(all_files, desc=f"📂 掃描中 {root.name[:10]}...", leave=False):
        rel_p = p.relative_to(root)
        files_data[rel_p] = {"path": p, "size": p.stat().st_size}
    return files_data, root

# ----------------功能模組----------------

def mode_compare_diff():
    """功能 1：比對兩個專案的結構差異"""
    path_a = input("\n👉 請輸入資料夾 A 路徑: ").strip()
    path_b = input("👉 請輸入資料夾 B 路徑: ").strip()
    
    data_a, _ = scan_dir(path_a)
    data_b, _ = scan_dir(path_b)
    
    all_paths = sorted(set(data_a.keys()) | set(data_b.keys()))
    print(f"\n{'狀態':<15} | {'相對路徑'}")
    print("-" * 60)
    
    for rel_p in all_paths:
        if rel_p in data_a and rel_p not in data_b:
            print(f"🔴 僅在 A 存在  | {rel_p}")
        elif rel_p not in data_a and rel_p in data_b:
            print(f"🟢 僅在 B 存在  | {rel_p}")
        else:
            if data_a[rel_p]['size'] != data_b[rel_p]['size']:
                print(f"🟡 內容不同     | {rel_p} (大小差異)")

def mode_cleanup_duplicates():
    """功能 2：深度清理單一資料夾內的重複檔案 (依內容)"""
    path_input = input("\n👉 請輸入要清理的資料夾路徑: ").strip()
    scan_root = Path(path_input).expanduser()
    
    # 建立回收區
    cleanup_folder = Path.home() / "Desktop" / f"Cleanup_{datetime.now().strftime('%m%d_%H%M')}"
    
    # 1. 大小分群
    files_data, _ = scan_dir(path_input)
    size_groups = defaultdict(list)
    for info in files_data.values():
        size_groups[info['size']].append(info['path'])
        
    potential_dupes = [paths for sz, paths in size_groups.items() if len(paths) > 1 and sz > 0]
    
    if not potential_dupes:
        print("✨ 沒發現任何重複檔案。")
        return

    # 2. 雜湊比對
    seen_hashes = {}
    to_move = []
    
    for path_list in tqdm(potential_dupes, desc="🧪 深度內容比對中"):
        for f_path in path_list:
            f_hash = get_file_hash(f_path)
            if f_hash in seen_hashes:
                to_move.append(f_path)
            else:
                seen_hashes[f_hash] = f_path

    # 3. 執行搬移
    if to_move:
        cleanup_folder.mkdir(parents=True, exist_ok=True)
        print(f"🚀 發現 {len(to_move)} 個重複檔案，準備搬移至桌面...")
        for f in tqdm(to_move, desc="📦 搬移檔案中"):
            dest = cleanup_folder / f.name
            if dest.exists(): dest = cleanup_folder / f"{datetime.now().microsecond}_{f.name}"
            shutil.move(str(f), str(dest))
        print(f"✅ 清理完成！存放在: {cleanup_folder}")
    else:
        print("✨ 內容皆不重複。")

# ----------------主選單----------------

def main_menu():
    while True:
        print(f"\n{'='*20} 專案管理 & 清理大師 {'='*20}")
        print("1. 🔍 比對兩個專案 (查看結構差異)")
        print("2. 🧹 清理單一專案 (刪除內容重複檔案)")
        print("0. 🚪 離開程式")
        print("="*55)
        
        choice = input("請選擇功能 (0-2): ").strip()
        
        if choice == '1':
            mode_compare_diff()
        elif choice == '2':
            mode_cleanup_duplicates()
        elif choice == '0':
            print("👋 再見！")
            break
        else:
            print("❌ 輸入錯誤，請重新選擇。")

if __name__ == "__main__":
    main_menu()