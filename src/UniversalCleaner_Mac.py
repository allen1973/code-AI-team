# -*- coding: utf-8 -*-
import os
import shutil
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def run_universal_cleanup():
    print("=== macOS 萬用重複檔案清理工具 ===")
    
    # 1. 設定掃描參數
    scan_root = input("👉 請輸入要清理的資料夾路徑: ").strip().replace("\\", "")
    if not os.path.exists(scan_root):
        print("❌ 路徑不存在。")
        return

    ext_input = input("👉 請輸入要清理的副檔名 (例如 pdf,jpg,png，留空則掃描所有檔案): ").lower()
    target_exts = set([f".{e.strip()}" for e in ext_input.split(',') if e.strip()]) if ext_input else None

    # 2. 設定回收區 (桌面)
    cleanup_folder = Path.home() / "Desktop" / f"Cleanup_Archive_{datetime.now().strftime('%Y%m%d_%H%M')}"
    cleanup_folder.mkdir(parents=True, exist_ok=True)
    log_file = cleanup_folder / "cleanup_report.csv"

    # 3. 檢索檔案
    print("🔍 正在檢索檔案...")
    all_files = []
    for p in Path(scan_root).rglob('*'):
        if p.is_file() and not p.name.startswith('._'):
            if target_exts is None or p.suffix.lower() in target_exts:
                all_files.append(p)
    
    seen_hashes = {}
    actions = []
    saved_size = 0

    # 4. 比對與分析
    for f_path in tqdm(all_files, desc="分析內容中"):
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

    # 5. 執行搬移
    if not actions:
        print("✨ 沒發現重複檔案！")
        return

    print(f"🚀 發現 {len(actions)} 個重複檔案，預計清出 {round(saved_size / (1024*1024), 2)} MB")
    
    with open(log_file, 'w', encoding='utf-8-sig', newline='') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=['檔案名稱', '原始路徑', '原因', '大小(MB)'])
        writer.writeheader()
        
        for act in actions:
            try:
                final_dest = act['dest']
                if final_dest.exists():
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
    print(f"✅ 清理完成！已移至桌面 {cleanup_folder.name}")
    print(f"💾 釋放空間：{round(saved_size / (1024*1024), 2)} MB")

if __name__ == "__main__":
    run_universal_cleanup()