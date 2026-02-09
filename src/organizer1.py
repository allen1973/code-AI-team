import shutil
from datetime import datetime
from pathlib import Path
from .engines import get_md5, predict_image_category

def run_image_ai_organizer(src_path, target_base, model, confidence=0.4, dry_run=True):
    src_dir = Path(src_path)
    target_base = Path(target_base)
    
    # 掃描檔案
    extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    all_files = [f for f in src_dir.rglob('*') if f.suffix.lower() in extensions]
    
    seen_md5s = {}
    
    for f_path in all_files:
        f_hash = get_md5(f_path)
        
        # 1. 去重判斷
        if f_hash and f_hash in seen_md5s:
            category = "system_duplicates"
        else:
            seen_md5s[f_hash] = f_path
            # 2. AI 辨識
            category = predict_image_category(model, f_path, confidence)
        
        dest_path = target_base / category / f_path.name
        
        # 執行搬移 (封裝原本的 dry_run 與衝突處理邏輯)
        execute_move(f_path, dest_path, dry_run)

def execute_move(src: Path, dst: Path, dry_run: bool):
    """執行搬移，包含衝突處理"""
    if dry_run:
        print(f"[預覽] {src.name} -> {dst}")
        return
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst = dst.with_name(f"{dst.stem}_{datetime.now().strftime('%H%M%S')}{dst.suffix}")
    
    shutil.move(str(src), str(dst))
