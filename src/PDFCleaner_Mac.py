# -*- coding: utf-8 -*-
import os
import shutil
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

def get_file_md5(file_path):
    """計算 PDF 檔案的指紋"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def run_pdf_cleanup():
    print("=== PDF 重複檔案自動清理工具 ===")
    
    # 1. 讓使用者輸入路徑
    scan_root = input("👉 請輸入要清理 PDF 的資料夾路徑: ").strip().replace("\\", "")
    if not os.path.exists(scan_root):
        print("❌ 路徑不存在。")
        return

    # 2. 設定回收區 (放在桌面)
    cleanup_folder = Path.home() / "Desktop" / f"PDF_Cleanup_Archive_{datetime.now().strftime('%Y%m%d_%H%M')}"
    cleanup_folder.mkdir(parents=True, exist_ok=True)
    log_file = cleanup_folder / "pdf_cleanup_log.csv"

    # 3. 搜尋所有 PDF 檔案
    all_files = [p for p in Path(scan_root).rglob('*') if p.suffix.lower() == '.pdf' and not p.name.startswith('._')]
    
    seen_hashes = {} # md5 -> first_path
    actions = []
    saved_size = 0 # 累計省下的空間

    print(f"🔍 正在掃描 {len(all_files)} 個 PDF 檔案...")

    for f_path in tqdm(all_files, desc="比對指紋中"):
        f_hash = get_file_md5(f_path)
        if not f_hash: continue

        if f_hash in seen_hashes:
            # 發現重複！
            f_size = f_path.stat().st_size
            saved_size += f_size
            actions.append({
                'file': f_path,
                'reason': f"與 {seen_hashes[f_hash]} 內容完全相同",
                'dest': cleanup_folder / f_path.name,
                'size_mb': round(f_size / (1024 * 1024), 2)
            })
        else:
            # 這是目前唯一的檔案
            seen_hashes[f_hash] = str(f_path)

    # 4. 執行搬移
    if not actions:
        print("✨ 恭喜！沒有發現任何重複的 PDF 檔案。")
        return

    print(f"🚀 發現 {len(actions)} 個重複檔案，預計可清出 {round(saved_size / (1024*1024), 2)} MB")
    
    with open(log_file, 'w', encoding='utf-8-sig', newline='') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=['檔案名稱', '原始路徑', '原因', '大小(MB)'])
        writer.writeheader()
        
        for act in actions:
            try:
                # 處理同名檔案搬移衝突
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
                print(f"搬移失敗: {act['file'].name} - {str(e)}")

    print("-" * 50)
    print(f"✅ 清理完成！")
    print(f"📦 已移出：{len(actions)} 個重複 PDF")
    print(f"💾 釋放空間：{round(saved_size / (1024*1024), 2)} MB")
    print(f"📂 詳情請見桌面資料夾：{cleanup_folder.name}")

if __name__ == "__main__":
    run_pdf_cleanup()