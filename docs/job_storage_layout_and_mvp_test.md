# Storage paths：依 `job_id` 落地 input / output（實作與 MVP 測試）

本文說明在現有 **FastAPI + `POST /api/remove-background`** 架構下，如何以環境變數 **`STORAGE_ROOT`** 為根目錄，為每個任務建立 **`input/{job_id}/`** 與 **`output/{job_id}/`**，並用 **curl** 或 **前端** 驗證檔案存在。

---

## 1. 目標目錄結構（驗收時要能在磁碟上看到）

設 **`STORAGE_ROOT`** 為環境變數（部署時設定；本機可只用預設值）。

```
{STORAGE_ROOT}/
  input/{job_id}/original.png    # 上傳留底（副檔名可依實作改為 .jpg / .webp，但須一致寫入）
  output/{job_id}/result.png     # 去背結果
```

- **`job_id`**：每個 HTTP 請求產生一個 **UUID**（建議 `uuid.uuid4()`），同一請求的 input/output 共用同一個 `job_id`。
- 程式內**不要寫死**絕對路徑；根目錄只來自 **`STORAGE_ROOT`**（程式內可僅提供本機預設，例如相對於專案目錄的 `./storage`）。

---

## 2. 與現有程式對應關係

| 項目 | 現有位置 | 調整方向 |
|------|----------|----------|
| 路由 | `backend/app/routes/images.py` | 在 `remove_background` 內：產生 `job_id`、建立目錄、寫入 input/output 檔案後，再回傳與現況相同的 PNG 回應（或另加 header，見下文）。 |
| 設定 | `backend/app/config.py` | 新增 `get_storage_root()`（或同等命名），讀取 `os.getenv("STORAGE_ROOT", "<本機預設>")`，並 `Path(...).resolve()`。 |
| 輔助（可選） | 新建 `backend/app/storage_paths.py`（建議） | 集中：`job_input_dir(root, job_id)`、`job_output_dir(...)`、`ensure_job_dirs(...)`，避免路由內到處拼字串。 |
| 忽略版本庫 | 專案根目錄 `.gitignore` | 加入預設本機儲存目錄（例如 `storage/`），避免測試圖被 commit。 |

應用程式進入點 **`backend/app/main.py`** 通常**不必改**，除非要在啟動時預先建立空目錄（一般也不需要）。

---

## 3. 實作步驟（Step by step）

### Step 1：環境變數與本機預設

1. 在 **`backend/app/config.py`** 新增讀取 **`STORAGE_ROOT`** 的函式。
2. 預設值僅供本機開發，例如：未設定時使用 **`./storage`**（相對於**啟動後端時的工作目錄**；建議文件註明「請在 `backend/` 目錄執行 uvicorn」或改為依 `__file__` 推專案根，二擇一並寫清楚）。
3. （可選）在 README 或 `.env.example` 加一行：`STORAGE_ROOT=/path/to/data`。

### Step 2：路徑與目錄建立

1. 新建 **`backend/app/storage_paths.py`**（名稱可自訂）：
   - 輸入：`storage_root: Path`, `job_id: str`。
   - 回傳：`input_dir = storage_root / "input" / job_id`，`output_dir = storage_root / "output" / job_id`。
   - 呼叫 **`input_dir.mkdir(parents=True, exist_ok=True)`** 與 **`output_dir.mkdir(...)`**（或一次建立兩層）。

### Step 3：在 `POST /api/remove-background` 內落地檔案

1. 在 **`read_and_validate_upload`** 成功取得 **`contents`** 之後，產生 **`job_id = str(uuid.uuid4())`**。
2. 解析或沿用既有邏輯得到圖片類型，決定 input 檔名：
   - **MVP 建議**：一律寫入 **`input/{job_id}/original.png`**（若上傳為 JPEG/WebP，仍可先寫原始 bytes 到 `original.jpg` / `original.webp`，但驗收路徑需與實作一致）；若你希望「路徑上一定是 `.png`」，可將上傳轉成 PNG 再存，或統一命名 **`original.png`** 僅在來源為 PNG 時使用。
   - **與本文開頭範例一致的最小約定**：至少保證 **`output/{job_id}/result.png`** 存在；input 建議 **`input/{job_id}/original.png`** 或帶正確副檔名之 **`original.*`**。
3. 將 **`contents`** 寫入 input 路徑（`open(..., "wb")`）。
4. 呼叫既有 **`remove(...)`** 得到 **`result` bytes。
5. 將 **`result`** 寫入 **`output/{job_id}/result.png`**。
6. 維持現有行為： **`return Response(content=result, media_type="image/png", ...)`**。
7. （建議）在 response header 加 **`X-Job-Id: <job_id>`**，方便測試時用同一個 id 找資料夾，無需改前端解析 body。

### Step 4：`.gitignore`

在 **`Life-Course-REMBG/.gitignore`**（或專案根目錄對應檔）加入：

```gitignore
storage/
```

（若本機預設目錄名稱不同，請改成相同名稱。）

### Step 5：錯誤處理（簡要）

- 若 **`STORAGE_ROOT`** 無法建立子目錄或無法寫入，應記錄 log 並回 **500**（與現有 rembg 失敗處理風格一致）。
- 寫入失敗時，避免回傳「成功」的 PNG；可選擇是否刪除半成品目錄（MVP 可略過）。

---

## 4. API 行為（實作完成後）

- **方法與路徑**：`POST /api/remove-background`（不變）。
- **請求**：`multipart/form-data`，欄位名 **`file`**（與現有 `images.py` 一致）。
- **回應**：主體仍為 **PNG 圖檔**；建議帶 **`X-Job-Id`**，對應磁碟上的 **`input/{job_id}/`** 與 **`output/{job_id}/`**。

---

## 5. MVP 測試方案（驗證「路徑上找得到檔」）[測試成功]

### 5.1 前置

1. 設定環境變數：

   - **Windows (PowerShell)**：`$env:STORAGE_ROOT = "D:\tmp\rembg-store"`
   - **Linux/macOS**：`export STORAGE_ROOT=/tmp/rembg-store`
   - 本機測試 `$env:STORAGE_ROOT` 無須設定。(避免 .gitignore 失效，導致大量測試檔案上傳)

2. 務必在 **`backend`** 目錄啟動 API（與你現有指令一致，例如 `uvicorn app.main:app --reload`）。
   - `cd` 至專案目錄後 `cd backend`
   - 進入虛擬環境 `conda activate Life-Course-REMBG`
   - 啟動API `uvicorn app.main:app --reload --port 8000`
   - 確認後端正常運作 `GET http://localhost:8000/health` → `200`

### 5.2 用 curl 測試 (Powershell/cmd) [測試成功]

1. 進入測試檔案放置區(請自行填入測試路徑)
   - `cd [your_test_folder]`

2. 執行 curl (Powershell/cmd)
```bash (Powershell)
curl -sS -D headers.txt -X POST "http://127.0.0.1:8000/api/remove-background" -F "file=@images2.jpg"
```
```bash (cmd)
curl.exe -sS -D headers.txt -X POST "http://127.0.0.1:8000/api/remove-background" -F "file=@images2.jpg"
```
- 在 your_test_folder 會產出 headers.txt

3. 確認 HTTP 狀態與 X-Job-Id (Powershell/cmd)
```bash (Powershell)
Get-Content ".\headers.txt"
```
```bash (cmd)
type headers.txt
```

4. 根據 X-Job-Id 查看結果

- input_path: `backend\{STORAGE_ROOT}\input\{X-Job-Id}\result.png`
- output_path: `backend\{STORAGE_ROOT}\input\{X-Job-Id}\result.png`

### 5.3 用前端測試 [測試成功]

1. 在 **`frontend/`**：
   - `npm run dev`（預設常為 `http://localhost:5173`，並將 `/api` proxy 至 `8000`）
2. 確認 **後端已先於 8000 埠運行**，否則 proxy 會失敗。
3. 在頁面上傳一張圖觸發去背
4. 從瀏覽器開發者工具 **Network** 查看 **`POST /api/remove-background`** 的 **Response Headers**，取得 **`X-Job-Id`**。
5. 到 **`STORAGE_ROOT`** 下依 **`input/{job_id}/`**、**`output/{job_id}/`** 檢查檔案是否存在。

### 5.4 驗收條件（Min MVP）[測試成功]

- 不論 **curl** 或 **前端**，完成一次成功去背後，在 **`{STORAGE_ROOT}/input/{id}/`** 與 **`{STORAGE_ROOT}/output/{job_id}/`** 都能看到對應檔案（**input 留底、output 結果**）。
- **`job_id`** 與該次請求對應（以 **`X-Job-Id`** 為準）。

---

## 6. 後續可選擴充（非 MVP 必須）

- **`GET /api/jobs/{job_id}/result.png`**：唯讀下載已落地檔案。
- **清理策略**：依時間或依 job 刪除舊目錄。
- **非同步任務**：若未來處理時間變長，再考慮 queue + 輪詢/ webhook，與目前同步 API 分開設計。

---

## 7. 檔案索引（實作時會動到的檔案）

- `backend/app/config.py` — `STORAGE_ROOT`
- `backend/app/storage_paths.py` — 新建（建議）
- `backend/app/routes/images.py` — 落地寫檔、`X-Job-Id`
- `.gitignore` — 忽略 `storage/`（或你的預設目錄）

完成以上步驟後，即可在固定 **`STORAGE_ROOT`** 下，用 **`input/{id}/`** 與 **`output/{id}/`** 完成追溯與除錯。
