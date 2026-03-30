# Backend 串接 Conda rembg 環境指引 (尚未確認)

## 目的

在 Conda 環境中安裝 `rembg` 與 FastAPI 相關依賴後，於本專案 `backend` 目錄執行 `uvicorn`，啟動 FastAPI 服務（`app.main:app`），提供 `POST /api/remove-background` 供前端或 curl 呼叫。

---

## 初次設定（本機尚未建立環境）

於 PowerShell 執行（路徑請改為本機專案實際位置）：

```powershell
conda create --name rembg python=3.11.5
conda activate rembg
pip install "rembg[cpu,cli]"
```

```powershell
rembg --help
rembg i --help
```

上述已於本機端測試可運行指令 rembg i [Input] [Output]

---
**以下階段接尚未確認**


於 PowerShell 執行（路徑請改為本機專案實際位置）：

```powershell
cd d:\ChingH100\APIgateway\Life-Course-Remove-Background\backend
pip install fastapi==0.135.1 uvicorn[standard]==0.30.6 python-multipart==0.0.22 pillow==12.1.1
```

第二段 `pip install` 僅補齊 FastAPI、uvicorn、`python-multipart`、Pillow；`rembg` 已由上一段安裝，勿重複安裝。

---

## 每次啟動 Backend

```powershell
conda activate rembg
cd d:\ChingH100\APIgateway\Life-Course-Remove-Background\backend
uvicorn app.main:app --reload --port 8000
```

成功時終端機應出現：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## 驗證

- 瀏覽器開啟：http://localhost:8000/docs  
- 去背 API：`POST http://localhost:8000/api/remove-background`（`multipart/form-data`，欄位 `file`）

```powershell
curl -X POST http://localhost:8000/api/remove-background -F "file=@你的圖片.jpg"
```

---

## 一併使用前端（本機開發）

另開終端機：

```powershell
cd d:\ChingH100\APIgateway\Life-Course-Remove-Background\frontend
npm install
npm run dev
```

瀏覽器開啟 http://localhost:5173 ；須先讓 Backend 在 `http://localhost:8000` 運行。

---

## 注意事項

1. 須在 `backend` 目錄執行 `uvicorn`，否則無法載入 `app` 模組。  
2. rembg 首次處理圖片時會下載模型（約 170 MB），耗時較長屬正常。  
3. `static/uploads`、`static/outputs` 於 Backend 啟動時自動建立。  
4. **本指引預設 `rembg[cpu,cli]`**（不需安裝 CUDA Toolkit／cuDNN，推理較慢但設定最簡）。若日後要改用 GPU，請改為 `pip install "rembg[gpu,cli]"` 並依 [onnxruntime GPU 說明](https://onnxruntime.ai/getting-started) 補齊驅動與 CUDA／cuDNN。
