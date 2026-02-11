# 外接硬碟自動化整理工具 – 跨平台規格書 v0.1

## 0. 實作優先順序（給 LLM 的總指令）

本規格的**第一階段目標**是：

> 實作一支「單檔 Python CLI：`disk_scan.py`」，  
> **跨平台** (Windows / macOS / Linux) 掃描外接硬碟，  
> 產出 `disk_report.csv` + 對應 OS 的移動腳本（`.bat` 或 `.sh`），  
> 過程**不直接刪除或移動檔案**。

**暫時不要實作：**

- REST API / FastAPI
- 資料庫（SQLite / Postgres）
- 複雜專案架構（多檔案、目錄結構）

---

## 1. 產品定位與使用情境

### 1.1 產品定位

- 專門處理：**USB 外接硬碟 / 備份碟**
- 解決問題：
  - 磁碟裡檔案種類混雜、關聯性複雜（Adobe / Web 專案）
  - 使用者只想先「看清楚有哪些重複檔案、可以刪什麼」，而不是馬上讓工具自動刪檔

### 1.2 典型情境

- **Scenario A：多年備份碟清理**
  - 混合 MOV / MP4 / PSD / AI / ZIP
  - 想找出「大顆重複檔案」來釋放空間

- **Scenario B：專案＋字型＋安裝檔混在一起**
  - 不同年份的專案資料夾、字型庫、軟體安裝檔全部丟在同一顆硬碟
  - 使用者要求：「專案資料夾絕對不能被動到」，只想動字型與安裝檔等

### 1.3 非支援範圍（MVP）

- 不解壓縮與掃描壓縮檔內容（ZIP / RAR…）
- 不掃描網路磁碟或雲端，只掃 OS 看得到的本機路徑（含外接碟）
- 建議單次掃描上限：**約 2TB 或 100 萬檔案**（超過請使用者分批掃描）

---

## 2. 執行環境與依賴

### 2.1 目標平台（跨平台）

- **Windows 10+**
- **macOS 13+** (Intel / Apple Silicon M1/M2/M3)
- **Linux Ubuntu 22+**

同一份 `disk_scan.py` 程式碼在所有平台上執行，無需修改。

### 2.2 Python 與依賴

- Python 3.10+
  - macOS：`brew install python@3.10`
  - Windows：從 python.org 下載或 `winget install python`
  - Linux：`apt install python3.10` 或 `apt install python3.11`
- 必要第三方套件：
  - `pandas`
  - `tqdm`
- 標準庫（全平台通用）：
  - `os`, `pathlib`, `hashlib`, `time`, `json`, `logging`, `argparse`, `platform`, `shutil`, `sys`

### 2.3 跨平台設計原則

#### 路徑處理

- **一律使用 `pathlib.Path`**，自動處理 Windows `\` vs Unix `/`
- 程式內部統一用 Path 物件操作，輸出時再轉換成字串

範例：

```python
from pathlib import Path

# 各平台傳入不同值，Path 自動處理
path = Path(user_input)  # Windows: "E:\BACKUP" → Path('E:\\BACKUP')
                          # macOS/Linux: "/Volumes/BACKUP" → Path('/Volumes/BACKUP')
```

#### 外接硬碟掛載點

- **Windows**：磁碟機代號（`D:\`, `E:\` 等）
- **macOS**：`/Volumes/` 下（例如 `/Volumes/BACKUP`, `/Volumes/My Disk`）
- **Linux**：`/mnt/` 或 `/media/` 下（例如 `/mnt/usb`, `/media/user/backup`）

#### 輸出腳本格式

程式**自動偵測 OS**，產生對應格式：

- **Windows**：`move_script.bat`
  ```bat
  @echo off
  move "E:\videos\a.mp4" "E:\staging\videos\a.mp4"
  ```

- **macOS / Linux**：`move_script.sh`
  ```bash
  #!/bin/bash
  mkdir -p "/Volumes/BACKUP/staging"
  mv "/Volumes/BACKUP/videos/a.mov" "/Volumes/BACKUP/staging/videos/a.mov"
  chmod +x move_script.sh
  ```

#### 隱藏 / 系統檔

各 OS 可能有系統檔需要略過（非必須，MVP 可先全掃）：

- **macOS**：`.DS_Store`, `.Trashes`, `.git` 等
- **Windows**：`System Volume Information`, `$Recycle.Bin`, `Thumbs.db` 等
- **Linux**：`.` 開頭的隱藏檔（通常掃描即可）

---

## 3. CLI 介面規格

### 3.1 執行方式

所有平台用相同指令格式（`pathlib` 自動轉換路徑）：

**macOS / Linux：**

```bash
python disk_scan.py \
  --path "/Volumes/BACKUP" \
  --mode "deep" \
  --whitelist-file "whitelist.txt" \
  --output-dir "./reports"
```

**Windows (PowerShell)：**

```powershell
python disk_scan.py `
  --path "E:\" `
  --mode "deep" `
  --whitelist-file "whitelist.txt" `
  --output-dir "./reports"
```

**Windows (cmd.exe)：**

```cmd
python disk_scan.py ^
  --path "E:\" ^
  --mode "deep" ^
  --whitelist-file "whitelist.txt" ^
  --output-dir "./reports"
```

或最簡單（所有平台統一）：

```bash
python disk_scan.py --path "/Volumes/BACKUP" --mode deep
```

### 3.2 參數定義

- `--path`（必填）
  - 要掃描的根目錄
  - Windows 範例：`"E:\"`, `"D:\BACKUP"`, `"\\?\E:\LongPath"` 等
  - macOS 範例：`"/Volumes/BACKUP"`, `"/Users/username/Desktop/test"`
  - Linux 範例：`"/mnt/usb"`, `"/media/user/backup"` 等
  - 若路徑包含空格，須用引號包起來

- `--mode`（選填，預設 `deep`）
  - `"index"`：快速索引，只列出檔案基本資料（不算 hash）
  - `"deep"`：深度分析，會算 hash、偵測重複檔案
  - `"audit"`：安全審計，強調專案相關檔案的標記（先可等同 `deep`，預留）

- `--whitelist-file`（選填）
  - 純文字檔，每行一個「白名單關鍵字或路徑片段」
  - 只要路徑中包含這些字串，就視為 **Protected 區域**
  - 若不指定，程式會自動用內建預設值

- `--output-dir`（選填，預設當前目錄下 `./reports/`）
  - 所有輸出檔案放在這裡：
    - `disk_report.csv`
    - `scan_log.txt`
    - `checkpoint.json`
    - `move_script.bat`（Windows）或 `move_script.sh`（macOS/Linux）

---


## 4. 檔案分類與保護邏輯

### 4.1 Category 分類規則（實際外接硬碟場景）

在掃描時，每個檔案自動套用以下「主分類」。
分類的目標是：協助使用者判斷「哪一類可以優先清、哪一類需要特別小心」。

| Category         | 代表副檔名（例）                                                             | 常見內容 / 場景                          |
|-----------------|-------------------------------------------------------------------------------|-----------------------------------------|
| Movie / Video   | `.mp4`, `.mov`, `.mkv`, `.avi`, `.m4v`                                       | 影片、螢幕錄影、相機錄影檔              |
| Photo / Image   | `.jpg`, `.jpeg`, `.png`, `.heic`, `.gif`, `.tif`, RAW：`.cr2`, `.nef`, `.arw` | 數位相片、截圖、設計輸出圖              |
| Audio / Music   | `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`                              | 音樂、Podcast、錄音檔                   |
| Document        | `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.txt`, `.md`     | 文件、簡報、筆記                        |
| Archive / Backup| `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, 備份檔：`*.backup`, `*.bak` 等         | 壓縮檔、歷史備份包                       |
| DiskImage / VM  | `.iso`, `.dmg`, `.vdi`, `.vmdk`, `.qcow2`                                    | 系統映像檔、虛擬機磁碟                   |
| Installer       | `.exe`, `.msi`, 作為安裝包的 `.dmg`, `.pkg`, `.AppImage`                    | 安裝程式、安裝包                         |
| Project         | `.psd`, `.psb`, `.ai`, `.indd`, `.fig`, `.sketch`, `.blend`, `.c4d`, `.prproj`, `.aep`, `.html`, `.css`, `.js`, `.ts`, `.vue`, `.jsx`, `.py`, `.ipynb` | 設計專案、3D 專案、剪輯專案、原始碼     |
| Fonts           | `.ttf`, `.otf`, `.woff`, `.woff2`                                            | 字型檔                                 |
| App / Library   | 資料夾名稱：`node_modules`, `venv`, `.venv`, `.git`, `Pods`, `.gradle` 等    | 程式相依套件、版本控制資料              |
| System / Cache  | `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.log`, `.Trashes`, `Cache` 資料夾       | 系統快取、暫存檔                         |
| Unknown         | 其他無法歸類或罕見副檔名                                                     | 來源不明 / 罕見專用格式                  |

> 實作建議：  
> - 先用「副檔名」判斷 Category。  
> - 若同時符合多個類別，以優先順序處理：`Project > Movie / Photo > 其他`。  
> - 路徑關鍵字（例如 `Photos`, `DCIM`, `Movies`, `Music`, `Projects`, `Adobe`）可作為輔助訊號，但非必須。

### 4.2 Protected / Free 區域判定

每個檔案有一個 **Status_Icon**：

- `🔴`：Protected（建議不動）
- `🟢`：Free（可考慮清理）

**Protected 判定條件（任一成立即可）：**

1. 檔案路徑中包含「白名單關鍵字」（來自 `--whitelist-file` 每一行字串）
2. 路徑中包含與專案相關關鍵字，例如：`Projects`, `Project`, `Client`, `Adobe`, `Web`, `Source`, `Repo`
3. Category 屬於以下幾種，預設視為敏感：
   - `Project`
   - `Document`
   - `Fonts`
4. 路徑包含明顯系統/版本控制目錄（例如 `.git`, `.svn`），為安全起見預設紅燈

> 實作建議：  
> - 若以上條件任一符合 → `Status_Icon = "🔴"`  
> - 否則 → `Status_Icon = "🟢"`  

### 4.3 `Action_Suggest` 預設邏輯（依 Category + Duplicate + Status）

`Action_Suggest` 可能值：

- `Keep`：建議保留，不進行搬移
- `Move_To_Staging`：建議搬到轉運站（staging），供使用者二次確認後再決定刪除
- `Ignore`：既不主動保留，也不主動建議搬移（例如單一正常文件）

**總原則：**

1. **紅燈優先安全**：`Status_Icon = 🔴` 時，一律 `Keep`
2. **綠燈才考慮類別與是否重複**

對於 `Status_Icon = 🟢` 的檔案，可用下表描述預設邏輯：

| Category          | Is_Duplicate = true                          | Is_Duplicate = false                                |
|------------------|-----------------------------------------------|-----------------------------------------------------|
| Movie / Video    | `Move_To_Staging`（大檔重複，優先清理）      | `Ignore`                                            |
| Photo / Image    | `Move_To_Staging`（重複照片可集中審核）      | `Ignore`                                            |
| Audio / Music    | `Move_To_Staging`（重複音樂可集中審核）      | `Ignore`                                            |
| Document         | `Keep`                                       | `Keep`                                              |
| Archive / Backup | `Move_To_Staging`（重複備份包可大幅省空間）  | `Keep`                                              |
| DiskImage / VM   | `Move_To_Staging`（重複映像檔可審核清理）    | `Keep`                                              |
| Installer        | `Move_To_Staging`（重複或單一都可清理）      | `Move_To_Staging`                                   |
| Project          | `Keep`                                       | `Keep`                                              |
| Fonts            | `Move_To_Staging`（重複字型可集中審核）      | `Keep`                                              |
| App / Library    | `Move_To_Staging`（多半可重建，清理風險低）  | 若 `Size_MB > 50` → `Move_To_Staging`，否則 `Ignore` |
| System / Cache   | `Move_To_Staging`（安全垃圾，可清）          | 若 `Size_MB > 10` → `Move_To_Staging`，否則 `Ignore` |
| Unknown          | `Ignore`                                     | `Keep`                                              |

對 LLM 的程式邏輯建議（伪碼）：

```python
if status_icon == "🔴":
    action = "Keep"
else:  # 綠燈
    if category in ["Project", "Document"]:
        action = "Keep"
    elif category in ["Movie", "Photo", "Audio"]:
        action = "Move_To_Staging" if is_duplicate else "Ignore"
    elif category in ["Archive", "DiskImage"]:
        action = "Move_To_Staging" if is_duplicate else "Keep"
    elif category == "Installer":
        action = "Move_To_Staging"
    elif category == "Fonts":
        action = "Move_To_Staging" if is_duplicate else "Keep"
    elif category == "AppLibrary":
        action = "Move_To_Staging" if (is_duplicate or size_mb > 50) else "Ignore"
    elif category == "SystemCache":
        action = "Move_To_Staging" if size_mb > 10 else "Ignore"
    else:  # Unknown
        action = "Ignore" if is_duplicate else "Keep"


**下一步：** 把這份規格貼給 LLM，開始實作第一版！



## 🧩 與現有工具的差異（Competitive Landscape）

市面上已經有不少檔案／相片整理工具，但多數不是為「外接硬碟大掃除」這個情境設計。本工具的定位，是在下列專案之間找到一個空隙：

### organize（tfeldmann/organize）

- Repo：<https://github.com/tfeldmann/organize>  
- 特色：以 YAML 規則檔驅動的檔案自動整理工具，可以定期排程執行，類似 Hazel / File Juggler 的跨平台 CLI 版。
- 差異：
  - organize 側重「長期、自動化歸檔」，會直接對檔案系統進行 move/rename/delete。
  - 本工具改走「一次性批次分析 + 匯出 CSV 報表 + 產生搬移腳本」的路線，分析階段完全唯讀，實際動作由使用者決定，對外接備份碟更安全。

### AI File Sorter（hyperfield/ai-file-sorter）

- Repo：<https://github.com/hyperfield/ai-file-sorter>  
- 特色：使用本地或雲端 LLM 智能分類檔案，提供桌面 GUI，使用者在 UI 中審核 AI 建議後才移動檔案。
- 差異：
  - AI File Sorter 側重「AI 分類 + 互動式 GUI」，分類標準較偏向語意而非專案安全。
  - 本工具目前不依賴 LLM 做語意分類，而是針對容量與風險（影片、備份包、Installer、專案檔等）做明確規則與建議，並特別強調「專案資料夾不可動」的白名單保護。

### TagStudio（TagStudioDev/TagStudio）

- Repo：<https://github.com/TagStudioDev/TagStudio>  
- 特色：在現有資料夾結構之上建立標籤與欄位系統，不強迫移動檔案，適合作為長期的個人資產管理工具。
- 差異：
  - TagStudio 像是「圖形化資產資料庫」，重點在長期管理與搜尋。
  - 本工具則是「離線磁碟清理助手」，核心輸出是可供試算與排序的 `disk_report.csv`，目標是幫你在數小時內完成一顆外接硬碟的大掃除，而不是建立長期標註系統。

### Photoview（photoview/photoview）

- Repo：<https://github.com/photoview/photoview>  
- 特色：自架相簿服務，直接掃描檔案系統路徑（含 NAS），產生縮圖、臉部辨識與 Web 相簿 UI，適合長期瀏覽與分享家用照片庫。
- 差異：
  - Photoview 主要解決「好看地瀏覽與分享照片」，不特別針對重複檔清理或空間回收。
  - 本工具專注在「找出可清理的大檔／重複檔」，透過 CSV 報表與 `Action_Suggest` 帶出具體的清理策略。

### Tagger（dicej/tagger）

- Repo：<https://github.com/dicej/tagger>  
- 特色：Web 版照片／影片整理工具，持續監控同步資料夾，支援合併 exact 與 inexact duplicate（例如不同解析度的同一張照片）。
- 差異：
  - Tagger 側重於「長期維護個人相片庫」，並在 Web UI 中處理去重與標籤。
  - 本工具則以「外接硬碟一次性盤點」為目標，不啟動常駐服務，只在你需要清理備份碟時啟動掃描，給出一次性的去重與清理建議。

---

### 總結：本工具的定位

相較於上述專案，本工具的幾個關鍵特點：

1. **針對外接備份碟的「一次性大掃除」**  
   - 不要求長期部署 server 或常駐程式，插上硬碟 → 掃描 → 看報表 → 執行搬移腳本，即可完成一次任務。

2. **分析階段完全唯讀，所有動作都透過腳本顯式執行**  
   - 掃描與去重階段不改動任何檔案，只產出 `disk_report.csv` 與 `move_script`，實際執行權完全在使用者手上。

3. **以「清空間」為導向的分類與建議邏輯**  
   - 清楚區分 Movie / Photo / Archive / Installer / Project 等實際硬碟大宗類型，
   - 預設保護專案、文件與字型，優先建議處理重複影片、備份包、Installer、node_modules 這類高容量、可重建資源。

4. **跨平台、單一 CLI 檔案、LLM 友善**  
   - 使用 `pathlib` 與標準庫，單一 `disk_scan.py` 在 Windows / macOS / Linux 三平台皆可執行，
   - 規格清楚，方便透過 LLM 協作維護與擴充。

### TL;DR：和其他工具一眼看懂的差異

| 專案              | 主要用途                     | 是否長期常駐 | 是否有 GUI       | 是否直接移動/刪檔 | 是否專為外接備份碟設計 |
|-------------------|------------------------------|--------------|------------------|--------------------|------------------------|
| 本工具（此專案）  | 外接硬碟一次性大掃除、去重   | 否           | 否（CLI + CSV）  | 否（只產腳本）     | 是                     |
| organize          | 規則式自動檔案整理           | 可排程長期   | 否（CLI）        | 是                 | 否（通用路徑）         |
| AI File Sorter    | AI 檔案分類＋互動式審核      | 否           | 是（桌面 GUI）   | 是                 | 否                     |
| TagStudio         | 長期資產管理（標籤＋欄位）   | 是           | 是（桌面 GUI）   | 視操作而定         | 否                     |
| Photoview         | 自架相簿、瀏覽＆分享照片     | 是           | 是（Web UI）     | 否（主打瀏覽）     | 否（主要是相片庫/NAS） |
| Tagger            | 照片/影片整理與去重（Web）   | 是           | 是（Web UI）     | 是（在 UI 內操作） | 否（主要是相片庫）     |
