# -*- coding: utf-8 -*-
import os
import shutil
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict

def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        # 增加緩衝區至 64KB，提升大檔案讀取效率
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def run_universal_cleanup():
    print("=== macOS 萬用重複檔案清理工具 (大檔案優化版) ===")
    
    # 1. 設定掃描參數
    path_input = input("👉 請輸入要清理的資料夾路徑: ").strip().replace("\\", "")
    scan_root = Path(path_input).expanduser()
    if not scan_root.exists():
        print("❌ 路徑不存在。")
        return

    ext_input = input("👉 請輸入要清理的副檔名 (例如 pdf,jpg，留空則全掃): ").lower()
    target_exts = set([f".{e.strip()}" for e in ext_input.split(',') if e.strip()]) if ext_input else None

    # 2. 設定回收區 (桌面)
    cleanup_folder = Path.home() / "Desktop" / f"Cleanup_Archive_{datetime.now().strftime('%Y%m%d_%H%M')}"
    cleanup_folder.mkdir(parents=True, exist_ok=True)
    log_file = cleanup_folder / "cleanup_report.csv"

    # 3. 第一階段：依檔案大小初步分群 (避免無意義的雜湊運算)
    print("🔍 正在檢索檔案並分析大小...")
    size_groups = defaultdict(list)
    
    # 獲取所有檔案列表
    raw_files = [p for p in scan_root.rglob('*') if p.is_file() and not p.name.startswith('._')]
    
    for p in raw_files:
        if target_exts is None or p.suffix.lower() in target_exts:
            size_groups[p.stat().st_size].append(p)

    # 4. 第二階段：僅針對「大小相同」的檔案進行 MD5 比對
    seen_hashes = {}
    actions = []
    saved_size = 0
    
    # 過濾出有潛在重複可能（大小相同）的群組
    potential_dupes = [paths for size, paths in size_groups.items() if len(paths) > 1 and size > 0]
    
    if not potential_dupes:
        print("✨ 沒發現任何大小相同的檔案，掃描結束。")
        return

    print(f"⚙️ 正在比對 {len(potential_dupes)} 組疑似重複的檔案內容...")
    
    for path_list in tqdm(potential_dupes, desc="深度比對中"):
        for f_path in path_list:
            f_hash = get_file_md5(f_path)
            if not f_hash: continue

            if f_hash in seen_hashes:
                f_size = f_path.stat().st_size
                saved_size += f_size
                actions.append({
                    'file': f_path,
                    'reason': f"內容與 {seen_hashes[f_hash]} 重複",
                    'dest': cleanup_folder / f_path.name,
                    'size_mb': round(f_size / (1024 * 1024), 2)
                })
            else:
                seen_hashes[f_hash] = str(f_path)

    # 5. 執行搬移與記錄
    if not actions:
        print("✨ 經過內容比對，未發現重複檔案！")
        return

    print(f"🚀 發現 {len(actions)} 個重複檔案，預計清出 {round(saved_size / (1024*1024), 2)} MB")
    
    with open(log_file, 'w', encoding='utf-8-sig', newline='') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=['檔案名稱', '原始路徑', '原因', '大小(MB)'])
        writer.writeheader()
        
        for act in actions:
            try:
                final_dest = act['dest']
                if final_dest.exists():
                    # 若檔名衝突，加上微秒區分
                    final_dest = cleanup_folder / f"{datetime.now().microsecond}_{act['file'].name}"
                
                shutil.move(str(act['file']), str(final_dest))
                writer.writerow({
                    '檔案名稱': act['file'].name,
                    '原始路徑': act['file'],
                    '原因': act['reason'],
                    '大小(MB)': act['size_mb']
                })
            except Exception as e:
                print(f"失敗: {act['file'].name} - {e}")

    print("-" * 50)
    print(f"✅ 清理完成！已移至：{cleanup_folder.name}")
    print(f"💾 釋放空間：{round(saved_size / (1024*1024), 2)} MB")

if __name__ == "__main__":
    run_universal_cleanup()