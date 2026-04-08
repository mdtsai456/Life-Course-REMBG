---
date: 2026-04-08
topic: zeabur-deploy-checklist
repo: Life-Course-REMBG
---

# Zeabur 部署清單（逐步點選／指令）

本文件假設：**同一個 Git repo**，在 Zeabur 建立 **兩個 Service**（`frontend` + `backend`），與本機 `frontend`（Vite）+ `backend`（FastAPI + rembg）對應。

## 0. 上線前必做（程式與設定）

### 0.1 後端：`backend/requirements.txt`

**本 repo 已包含** `backend/requirements.txt`；Zeabur Python 建置時以 `pip install -r requirements.txt` 安裝下列依賴（版本未鎖定，由解析結果決定）。若需調整套件或鎖版，請直接編輯該檔後再部署。

```text
fastapi[standard]
uvicorn[standard]
python-multipart
rembg
pillow
```

選做 — 本機驗證（可在 CI 或 Zeabur 上驗證代替）：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
curl -s http://127.0.0.1:8000/health
```

### 0.2 前端：Production 的 API 網址（不可再依賴 dev proxy）

開發時 `vite.config.js` 把 `/api` 轉到 `localhost:8000`；**打包後沒有這個 proxy**，瀏覽器會對「前端網域」發 `/api`，除非你做閘道轉發，否則會 404。

**已實作**：`frontend/src/services/api.js` 內 `removeBackgroundApiUrl()` 會讀取 `import.meta.env.VITE_API_BASE_URL`，先對字串 **trim** 再移除**所有**尾端 `/`；未設定或僅空白時仍使用相對路徑 `/api/...`（本機 Vite proxy），避免 Zeabur 變數貼上時多空白或斜線。

**部署時請**：

1. 在 Zeabur **前端 Service** 的 **Variables** 設定 `VITE_API_BASE_URL` = 後端 Service 的 **HTTPS 根網址**（建議無結尾 `/`；多餘斜線由前端正規化），例如 `https://你的後端.xxx.zeabur.app`。
2. 每次變更 `VITE_*` 後需 **重新 build／Redeploy 前端**。

（後端路由為 `POST /api/remove-background`，完整請求 URL 為 `${VITE_API_BASE_URL}/api/remove-background`。）

### 0.3 後端：CORS

`backend/app/config.py` 讀取 `CORS_ALLOWED_ORIGINS`（預設僅 `http://localhost:5173`）。

在 Zeabur **後端 Service** 設定：

```text
CORS_ALLOWED_ORIGINS=https://你的前端.zeabur.app
```

若有多個來源（預覽網域等），用英文逗號分隔、無空白或多個網域：

```text
CORS_ALLOWED_ORIGINS=https://a.zeabur.app,https://b.zeabur.app
```

### 0.4 後端：儲存與文件（選用）

| 變數 | 說明 |
|------|------|
| `STORAGE_ROOT` | 預設 `./storage`；Zeabur 容器檔案系統多為 **暫存**，重啟可能清空。若僅 MVP 可接受；要持久化需接 Zeabur 的 Volume／物件儲存（規劃另議）。 |
| `DOCS_ENABLED` | 上線建議 `false`，關閉 `/docs`、`/redoc`。 |
| `REMOVE_BG_TIMEOUT` | 視方案 CPU／圖片大小調整（秒）。 |

---

## 1. Zeabur：建立專案與連接 Git

1. 登入 [Zeabur](https://zeabur.com)。
2. **Create new project**（名稱自訂）。
3. **Deploy new service** → 選 **Git** → 授權並選此 repo。
4. 之後會為 **同一個 repo** 各建立一次 Service（前端一次、後端一次），共兩個 Service。

---

## 2. Service A：後端（Python / FastAPI）

### 2.1 建立服務

1. 在 Project 內 **Add Service** → **Git** → 同一個 repository。
2. 服務名稱建議：`backend`（自訂即可）。

### 2.2 根目錄與 Watch path

- **Root Directory**（或 Zeabur 上對應欄位）：`backend`
- **Watch Paths**（若有）：僅 `backend/**`，避免前端變更觸發後端重建。

### 2.3 Build／Start（若自動偵測失敗時手動填）

Zeabur 常會自動偵測 Python；若需手動：

- **Build command**（示例）：`pip install -r requirements.txt`
- **Start command**（示例）：

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

（`PORT` 由平台注入；若介面不展開變數，改用 Zeabur 文件建議的 port 寫法。）

### 2.4 環境變數（後端 Service）

在該 Service 的 **Variables** 設定至少：

| Key | Value 範例 |
|-----|------------|
| `CORS_ALLOWED_ORIGINS` | `https://（前端部署後的網址）` |
| `DOCS_ENABLED` | `false` |

部署完成後，在 Zeabur 複製此 Service 的 **公開 HTTPS URL**，供前端 `VITE_API_BASE_URL` 使用。

### 2.5 健康檢查

瀏覽器或本機：

```bash
curl -sS "https://你的後端網址/health"
```

預期 JSON 內 `checks.rembg` 在模型載入後為 `true`（首次冷啟動可能稍久）。

---

## 3. Service B：前端（Node / Vite）

### 3.1 建立服務

1. **Add Service** → **Git** → 同一 repository。
2. 名稱建議：`frontend`。

### 3.2 根目錄與 Watch path

- **Root Directory**：`frontend`
- **Watch Paths**：僅 `frontend/**`

### 3.3 環境變數（需在第一次 build 前設定）

| Key | Value |
|-----|--------|
| `VITE_API_BASE_URL` | `https://你的後端.zeabur...`（與 2.4 一致，**無**結尾 `/`） |

若先 deploy 前端才拿到後端網址：先部署後端 → 複製後端 URL → 設好 `VITE_API_BASE_URL` → **Redeploy** 前端。

### 3.4 Build／Output（若自動偵測失敗時手動填）

- **Build command**：`npm ci && npm run build`（或 `npm install && npm run build`）
- **靜態輸出目錄**：`dist`（Vite 預設）

Zeabur 對 Node/Vite 多數會自動處理；若畫面 404 on refresh，再查 Zeabur 對 SPA 的 fallback 設定。

### 3.5 驗證

1. 開前端 HTTPS URL。
2. DevTools → Network：上傳圖片時，請求應打到 **後端網域** 的 `/api/remove-background`，且狀態 200。

---

## 4. 本機模擬「雲端」行為（選做）

在 `frontend` 目錄：

```bash
export VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run build
npm run preview
```

後端本機 `CORS_ALLOWED_ORIGINS` 需包含 `http://localhost:4173`（或 preview 實際埠）。

---

## 5. 已知限制與風險（部署時心裡有數）

- **rembg**：映像檔偏大、記憶體與冷啟動時間偏高；免費方案可能緩慢或 OOM，必要時升級方案或限流。
- **STORAGE_ROOT**：無持久 Volume 時，重啟後磁碟上的 job 目錄可能消失。
- **機密**：目前無登入；若 URL 公開，等同公開 API，需自行評估滥用與成本。

---

## 6. 完成檢查表（勾選用）

- [ ] `backend/requirements.txt` 已在 repo 中；Zeabur 或本機 `uvicorn` 可啟動
- [ ] Zeabur 前端已設定 `VITE_API_BASE_URL` 指向後端，且已重新 build
- [ ] 後端 `CORS_ALLOWED_ORIGINS` 含前端正式網址
- [ ] 後端 `DOCS_ENABLED=false`（若不想公開 OpenAPI）
- [ ] 兩個 Service 的 Root Directory 分別為 `backend` / `frontend`
- [ ] Watch paths 已分離，避免無關 redeploy
- [ ] `/health` 與實際去背流程在 Zeabur 上測過

---

## Next Steps

依賴清單與 `VITE_API_BASE_URL` 行為已在 repo 內。後續可選：在 GitHub Actions 加上 `pip install` + 靜態檢查／漏洞掃描、或依 Zeabur 文件調整資源與持久化儲存；新功能需求再執行 `/ce:brainstorm` 或 `/ce:plan`。
