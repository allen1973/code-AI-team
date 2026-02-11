import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from tkinter import filedialog, messagebox, Tk
from tqdm import tqdm
import fitz  # pip install pymupdf (更快、更穩定)
from multiprocessing import Pool, cpu_count
import sys

# 工業級日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("process.log", encoding="utf-8")]
)

def get_file_metadata(args: tuple) -> Dict:
    """單一檔案元數據提取 (多執行緒友好)"""
    file_path, dry_run = args
    meta = {
        "檔案名稱": file_path.name,
        "頁數": 0,
        "內容摘要": "等待掃描",
        "修改日期": "未知",
        "完整路徑": str(file_path.absolute())
    }
    try:
        if not file_path.exists():
            meta["內容摘要"] = "檔案不存在"
            return meta
        stats = file_path.stat()
        meta["修改日期"] = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        if dry_run:
            meta["內容摘要"] = "[Dry Run] 模擬完成"
            return meta
        
        # PyMuPDF 超快讀取
        doc = fitz.open(file_path)
        meta["頁數"] = len(doc)
        if meta["頁數"] > 0:
            text = doc[0].get_text().replace("\n", " ")[:50].strip()
            meta["內容摘要"] = text if text else "影像 PDF"
        doc.close()
    except Exception as e:
        logging.error(f"處理失敗 {file_path.name}: {str(e)}")
        meta["內容摘要"] = f"錯誤: {str(e)[:30]}"
    return meta

class PDFAutomationTool:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.logger = logging.getLogger("PDFTool")
        self.results = []

    def run(self):
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        source_dir = filedialog.askdirectory(title="選擇 PDF 資料夾")
        if not source_dir:
            return
        
        source_path = Path(source_dir)
        pdf_files = list(source_path.rglob("*.pdf"))
        if not pdf_files:
            messagebox.showwarning("提示", "未找到 PDF 檔案！")
            return
        
        self.logger.info(f"模式: {'[模擬]' if self.dry_run else '[正式]'} | 檔案數: {len(pdf_files)} | CPU 核心: {cpu_count()}")
        
        # 並行處理 (自動使用所有 CPU 核心)
        with Pool(processes=cpu_count()) as pool:
            args = [(f, self.dry_run) for f in pdf_files]
            results = list(tqdm(pool.imap(get_file_metadata, args), total=len(pdf_files), desc="處理進度"))
        
        self.results = [r for r in results if r["內容摘要"] != "檔案不存在"]  # 過濾無效檔案
        
        # 匯出 CSV
        df = pd.DataFrame(self.results)
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"PDF報告_{datetime.now().strftime('%m%d')}.csv"
        )
        if save_path:
            df.to_csv(save_path, index=False, encoding="utf-8-sig")
            self.logger.info(f"完成！儲存至: {save_path} | 有效筆數: {len(df)}")
            messagebox.showinfo("完成", f"處理 {len(df)} 筆資料")

if __name__ == "__main__":
    app = PDFAutomationTool(dry_run=False)  # 先用 True 測試
    app.run()
