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

## 目前限制 / Current Limitations

- 一次只處理一張上傳圖片
- 沒有 authentication 或 user account 模型
- 處理流程是同步的，每個 request 都會等待後端回應
- 沒有 job queue，也沒有額外的結果查詢 API，只有即時下載回應

## 補充 / Notes

- 後端 API 位於 `http://localhost:8000`
- 前端開發伺服器位於 `http://localhost:5173`
