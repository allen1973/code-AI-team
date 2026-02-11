# -*- coding: utf-8 -*-
"""
FontCleaner_Windows.py
功能：自動辨識重複與舊版字體，並安全移至 Windows 桌面回收區
"""

import os
import shutil
import csv
import hashlib
from pathlib import Path
from datetime import datetime
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
        return None

def get_font_info(file_path):
    """取得字體全名與版本號"""
    try:
        # Windows 路徑需使用 str 轉換，確保相容性
        font = TTFont(str(file_path), fontNumber=0, lazy=True)
        names = font['name']
        # ID 4: Full Name, ID 5: Version
        # 優先嘗試 Windows 平台的編碼 (Platform ID 3)
        full_name = names.getName(4, 3, 1, 1033) or names.getName(4, 1, 0, 0)
        version = names.getName(5, 3, 1, 1033) or names.getName(5, 1, 0, 0)
        font.close()
        return str(full_name) if full_name else None, str(version) if version else None
    except Exception:
        return None, None

def run_cleanup():
    print("=== Windows 字體自動清理工具 ===")
    
    # 1. 讓使用者輸入路徑 (移除 macOS 的 .replace("\\", ""))
    raw_path = input("👉 請輸入要掃描的資料夾路徑 (例如 D:\\Fonts): ").strip()
    # 處理 Windows 複製路徑時可能帶有的引號
    scan_root = raw_path.replace('"', '').replace("'", "")
    
    if not os.path.exists(scan_root):
        print(f"❌ 路徑不存在 ({scan_root})，請重新執行。")
        return

    # 2. 設定回收區 (Windows 桌面路徑)
    desktop_path = Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))
    cleanup_folder = desktop_path / f"Font_Cleanup_Archive_{datetime.now().strftime('%Y%m%d_%H%M')}"
    cleanup_folder.mkdir(parents=True, exist_ok=True)
    log_file = cleanup_folder / "cleanup_log.csv"

    font_exts = {'.ttf', '.otf', '.ttc'}
    # Windows 不需要排除 ._ 開頭的檔案，但建議排除系統隱藏檔
    all_files = [p for p in Path(scan_root).rglob('*') if p.suffix.lower() in font_exts]

    seen_md5 = {}        # md5 -> first_path
    seen_names = {}      # font_name -> (version, path)
    actions = []

    print(f"🔍 正在分析 {len(all_files)} 個檔案...")

    for f_path in tqdm(all_files, desc="處理中"):
        f_hash = get_file_md5(f_path)
        f_name, f_ver = get_font_info(f_path)

        reason = ""
        target_action = "KEEP"

        if f_hash in seen_md5:
            target_action = "MOVE"
            reason = f"完全重複 (與 {seen_md5[f_hash].name} 相同)"
        
        elif f_name and f_name in seen_names:
            old_ver, old_path = seen_names[f_name]
            # 簡單的版本號比對（字串比對）
            if f_ver and old_ver and f_ver > old_ver:
                actions.append({
                    'file': old_path,
                    'action': 'MOVE',
                    'reason': f"發現新版本 ({f_ver} > {old_ver})",
                    'dest': cleanup_folder / old_path.name
                })
                seen_names[f_name] = (f_ver, f_path)
                seen_md5[f_hash] = f_path
            else:
                target_action = "MOVE"
                reason = f"已有較新或同版本 ({old_ver})"
        
        else:
            seen_md5[f_hash] = f_path
            if f_name: seen_names[f_name] = (f_ver, f_path)

        if target_action == "MOVE":
            actions.append({
                'file': f_path,
                'action': 'MOVE',
                'reason': reason,
                'dest': cleanup_folder / f_path.name
            })

    # 3. 執行移動與記錄
    print(f"\n🚀 正在搬移 {len(actions)} 個多餘檔案至桌面回收區...")
    
    with open(log_file, 'w', encoding='utf-8-sig', newline='') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=['原始路徑', '處置', '原因'])
        writer.writeheader()
        
        for act in actions:
            try:
                # 如果回收區已有同名檔案，加上時間戳
                final_dest = act['dest']
                if final_dest.exists():
                    final_dest = final_dest.with_name(f"{datetime.now().microsecond}_{final_dest.name}")
                
                shutil.move(str(act['file']), str(final_dest))
                writer.writerow({'原始路徑': str(act['file']), '處置': '已移至回收區', '原因': act['reason']})
            except Exception as e:
                writer.writerow({'原始路徑': str(act['file']), '處置': '失敗', '原因': str(e)})

    print("-" * 50)
    print(f"✅ 清理完成！")
    print(f"📦 已移出檔案：{len(actions)} 個")
    print(f"📂 詳情與日誌請見桌面資料夾：{cleanup_folder.name}")

if __name__ == "__main__":
    run_cleanup()