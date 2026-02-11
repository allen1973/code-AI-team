import logging
import pandas as pd
import sys
import tkinter as tk
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from tkinter import filedialog, messagebox
from tqdm import tqdm
import PyPDF2

# --- 工業級日誌配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler("process.log", encoding="utf-8")]
)

class PDFAutomationTool:
    """
    Python 工程獅出品：工業級 PDF 自動化整理工具
    支援：跨平台、Dry Run、進度追蹤、外接硬碟優化
    """
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.logger = logging.getLogger("PDFTool")
        self.results = []
        
    def _get_file_metadata(self, file_path: Path) -> Dict:
        """【除錯官】嚴謹的元數據提取，預防 I/O 延遲與權限報錯"""
        meta = {
            "檔案名稱": file_path.name,
            "頁數": 0,
            "內容摘要": "等待掃描",
            "修改日期": "未知",
            "完整路徑": str(file_path.absolute())
        }
        try:
            if not file_path.exists():
                raise FileNotFoundError("檔案已移除或路徑失效")

            stats = file_path.stat()
            meta["修改日期"] = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

            # 只有在非 Dry Run 時才深入讀取內容，保護硬碟效能
            if not self.dry_run:
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    meta["頁數"] = len(reader.pages)
                    if meta["頁數"] > 0:
                        text = reader.pages[0].extract_text()
                        meta["內容摘要"] = text.replace("\n", " ")[:50].strip() if text else "影像格式"
            else:
                meta["內容摘要"] = "[Dry Run] 模擬讀取完成"
                
        except Exception as e:
            self.logger.error(f"處理失敗 {file_path.name}: {str(e)}")
            meta["內容摘要"] = f"錯誤: {str(e)}"
        
        return meta

    def run(self):
        """【架構師】主執行流程：GUI 交互與批次處理"""
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True) # 確保視窗在最前方

        # 1. 獲取目錄
        source_dir = filedialog.askdirectory(title="選擇 PDF 資料夾 (支援外接硬碟)")
        if not source_dir:
            self.logger.info("使用者取消操作")
            return

        source_path = Path(source_dir)
        pdf_files = list(source_path.rglob("*.pdf"))

        if not pdf_files:
            messagebox.showwarning("提示", "找不任何 PDF 檔案！")
            return

        self.logger.info(f"模式: {'[模擬執行]' if self.dry_run else '[正式執行]'}")
        self.logger.info(f"目標數量: {len(pdf_files)}")

        # 2. 核心處理循環 (帶進度條)
        for f in tqdm(pdf_files, desc="處理進度", unit="份"):
            self.results.append(self._get_file_metadata(f))

        # 3. 匯出成果
        df = pd.DataFrame(self.results)
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 檔案", "*.csv")],
            title="儲存報表",
            initialfile=f"PDF整理報告_{datetime.now().strftime('%m%d')}.csv"
        )

        if save_path:
            # utf-8-sig 解決 Excel 亂碼問題
            df.to_csv(save_path, index=False, encoding="utf-8-sig")
            self.logger.info(f"報告已存至: {save_path}")
            messagebox.showinfo("完成", f"處理完畢！\n總數：{len(df)} 筆\n模式：{'模擬' if self.dry_run else '正式'}")

if __name__ == "__main__":
    # --- 操作指南 ---
    # 建議先以 dry_run=True 測試路徑與數量
    # 正式處理請改為 dry_run=False
    app = PDFAutomationTool(dry_run=False) 
    app.run()