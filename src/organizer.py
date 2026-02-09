# src/organizer.py
from datetime import datetime
import csv
from pathlib import Path
from .engines import analyze_and_filter

def run_font_audit(scan_root, report_folder, min_glyph_threshold, dry_run=True):
    src, dest = Path(scan_root), Path(report_folder)
    files = [f for f in src.rglob('*') if f.suffix.lower() in {'.ttf', '.otf', '.ttc'}]
    
    if dry_run:
        print(f"🧪 [預覽模式] 發現 {len(files)} 個檔案")
        return

    dest.mkdir(parents=True, exist_ok=True)
    csv_path = dest / f"Font_Risk_Report_{datetime.now().strftime('%m%d_%H%M')}.csv"

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = ['Name', 'Risk_Tag', 'Lang', 'Count', 'License', 'Size_MB', 'Path']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for fpath in files:
            writer.writerow(analyze_and_filter(fpath, min_glyph_threshold))
