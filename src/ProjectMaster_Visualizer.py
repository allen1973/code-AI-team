# -*- coding: utf-8 -*-
import os
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# --- 支援預覽的圖片格式 ---
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

def generate_html_report(diff_data, path_a, path_b, output_path):
    """產生視覺化 HTML 報告"""
    html_template = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>專案差異預覽報告</title>
        <style>
            body { font-family: sans-serif; background: #f4f4f9; padding: 20px; }
            h1 { color: #333; }
            .card { background: white; border-radius: 8px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .tag { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; color: white; }
            .tag-only-a { background: #e74c3c; }
            .tag-only-b { background: #2ecc71; }
            .tag-diff { background: #f1c40f; color: #333; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }
            img { max-width: 200px; max-height: 200px; border: 1px solid #ccc; border-radius: 4px; display: block; margin-top: 5px; }
            .path-text { color: #666; font-size: 13px; word-break: break-all; }
        </style>
    </head>
    <body>
        <h1>🔍 專案結構差異報告</h1>
        <p>報告生成時間: {time}</p>
        <div class="card">
            <strong>專案 A:</strong> {path_a}<br>
            <strong>專案 B:</strong> {path_b}
        </div>
        <table>
            <tr><th>類型</th><th>檔案資訊 (相對路徑)</th><th>預覽 (如果是圖片)</th></tr>
            {rows}
        </table>
    </body>
    </html>
    """
    
    rows = ""
    for item in diff_data:
        tag_class = "tag-only-a" if "僅在 A" in item['type'] else "tag-only-b" if "僅在 B" in item['type'] else "tag-diff"
        
        # 判斷是否為圖片，若是則加入 <img> 標籤 (使用絕對路徑讓本地瀏覽器讀取)
        img_html = ""
        if item['full_path'] and Path(item['full_path']).suffix.lower() in IMG_EXTS:
            img_html = f'<a href="file://{item["full_path"]}" target="_blank"><img src="file://{item["full_path"]}"></a>'
        
        rows += f"""
        <tr>
            <td><span class="tag {tag_class}">{item['type']}</span></td>
            <td>
                <strong>{item['rel_path']}</strong><br>
                <span class="path-text">{item['info']}</span>
            </td>
            <td>{img_html}</td>
        </tr>
        """
    
    final_html = html_template.format(
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        path_a=path_a,
        path_b=path_b,
        rows=rows
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

# --- (其餘掃描與比對邏輯與前述相同，但在比對時記錄資料) ---

def mode_visual_compare():
    path_a = input("\n👉 請輸入資料夾 A 路徑: ").strip()
    path_b = input("👉 請輸入資料夾 B 路徑: ").strip()
    
    # 這裡調用之前的 scan_dir 邏輯... (略，假設已取得 data_a, data_b)
    # ... 比對邏輯 ...
    
    diff_list = [] # 用來存給 HTML 用的資料
    # 範例：diff_list.append({'type': '僅在 A 存在', 'rel_path': 'cat.png', 'full_path': '/path/to/a/cat.png', 'info': '1.2MB'})
    
    # 比對完成後
    report_file = Path.home() / "Desktop" / "Diff_Report.html"
    generate_html_report(diff_list, path_a, path_b, report_file)
    print(f"✅ HTML 報告已產生在桌面：{report_file}")
    os.system(f"open '{report_file}'") # 自動開啟瀏覽器 (macOS)