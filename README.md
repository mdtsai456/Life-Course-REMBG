# Life Course: Remove-Background

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
 
pip install -r backend/requirements.txt
 
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

## Docker（區網分享）

- **目的**：在本機 Docker 上以**單一 HTTP 埠**同時提供前端與 API（Nginx 反向代理），方便同一 Wi‑Fi 下的手機或其他電腦連線。
- **前置**：已安裝 Docker Desktop（Windows 建議啟用 WSL2 後端；macOS / Linux 直接使用）。
- **啟動**（repo 根目錄）：

```bash
docker compose up -d --build
```

- **本機瀏覽**：`http://localhost:8080/`（若將 compose 埠改為 `80:8080`，則為 `http://localhost/`）。
- **區網裝置**：在 Windows 以 `ipconfig` 查 IPv4，於手機／其他電腦開 `http://<該IPv4>:8080/`。
- **防火牆**：視需要允許 **TCP 8080**（或你映射的埠）於「私人網路」連入。
- **前端 API 基底網址**：與 Zeabur 不同，此模式**不必**設定 `VITE_API_BASE_URL`（未設定時前端使用相對路徑 `/api/...`）。
- **處理逾時**：後端以環境變數 `REMOVE_BG_TIMEOUT`（秒，預設 `60`）限制單次去背時間（見 `backend/app/config.py`）。Nginx 的 `proxy_read_timeout`／`proxy_send_timeout` 必須**大於**你設定的 `REMOVE_BG_TIMEOUT` 並預留餘量；預設 `frontend/nginx.docker.conf` 使用 300s。若只調高 `REMOVE_BG_TIMEOUT` 而未同步調整 Nginx 設定並重建 `web` 映像，客戶端可能先收到 **502**。
- **與 Zeabur 文件分工**：雲端雙服務部署仍見 `docs/plans/2026-04-08-zeabur-deploy-checklist.md`。

## 目前限制 / Current Limitations

- 一次只處理一張上傳圖片
- 沒有 authentication 或 user account 模型
- 處理流程是同步的，每個 request 都會等待後端回應
- 沒有 job queue，也沒有額外的結果查詢 API，只有即時下載回應

