# Life Course REMBG

- 預覽原圖與去背結果
- 限制檔案大小為 10 MB
- 將輸出下載為透明背景 PNG
- 使用 `GET /health` 檢查後端是否就緒

## 快速開始 / Quick Start

### 前置需求 / Prerequisites

- Node.js
- Conda
- Python 3.11

### 前端 / Frontend

```bash
cd frontend
npm install
npm run dev
```

前端會在 `http://localhost:5173` 啟動。

### 後端 / Backend

```bash
conda create -n rembg python=3.11.15
conda activate rembg
 
pip install "rembg[cpu,cli]"
pip install "fastapi[standard]"
 
cd backend
uvicorn app.main:app --reload
```

後端會在 `http://localhost:8000` 啟動。

前端開發伺服器會將 `/api` 請求代理到 `http://localhost:8000`。

## 雲端部署（Zeabur）與正式環境 API / Zeabur & production API

- 逐步操作與 Zeabur 後台設定請見：`docs/plans/2026-04-08-zeabur-deploy-checklist.md`。
- **本機開發**：不必設定 `VITE_API_BASE_URL`；前端會對同源路徑 `/api/...` 發請求，由 Vite dev server 轉到後端。
- **正式建置**（例如 Zeabur 前端 Service）：在 build 前設定環境變數 `VITE_API_BASE_URL` 為後端的 **HTTPS 根網址**（無結尾 `/`），例如 `https://your-backend.xxx.zeabur.app`，再執行 `npm run build`。變更後需重新 build。
- **後端 CORS**：部署時請設定 `CORS_ALLOWED_ORIGINS` 為前端的正式網址（多個以英文逗號分隔）。詳見 `backend/app/config.py`。

For Zeabur: use two services from the same repo with root directories `frontend` and `backend`. See the checklist above for variables, watch paths, and verification.

## 目前限制 / Current Limitations

- 一次只處理一張上傳圖片
- 沒有 authentication 或 user account 模型
- 處理流程是同步的，每個 request 都會等待後端回應
- 沒有 job queue，也沒有額外的結果查詢 API，只有即時下載回應

## 補充 / Notes

- 後端 API 位於 `http://localhost:8000`
- 前端開發伺服器位於 `http://localhost:5173`

