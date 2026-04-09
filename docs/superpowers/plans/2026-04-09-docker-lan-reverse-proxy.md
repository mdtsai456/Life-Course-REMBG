# Docker 區網部署（Windows 主機、Nginx 單一入口）實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 repo 根目錄提供 `docker compose` 流程：兩個服務 `backend`（FastAPI + rembg）與 `web`（Nginx + 前端 `dist`），對外僅暴露 `web` 的 HTTP 埠；區網裝置以 `http://<主機IP>:<埠>/` 使用，且 **`VITE_API_BASE_URL` 可不設**（前端走相對路徑 `/api/remove-background`，見 `frontend/src/services/api.js`）。

**架構：** `web` 將 `/api/` 與 `/health` 反向代理至 `backend:8000`；FastAPI 路由已為 `POST /api/remove-background` 與 `GET /health`（`backend/app/routes/images.py`、`backend/app/main.py`）。本機 Vite 的 `/api` 代理（`frontend/vite.config.js`）僅供開發；正式容器內由 Nginx 承接相同路徑語意。

**技術棧：** Docker、Docker Compose、`python:3.11-slim`、`node`（建置階段）、`nginxinc/nginx-unprivileged:alpine`（執行階段）、pip、`npm ci`。

**對照規格：** `docs/superpowers/specs/2026-04-09-docker-lan-reverse-proxy-design.md`

**實作狀態：** `backend/Dockerfile`、`frontend/Dockerfile`、`frontend/nginx.docker.conf`、`docker-compose.yml` 與 README「Docker（區網）」一節已合併於主線；下列 Task 核取方塊標為完成表示**交付物已在 repo**，手動驗證步驟（`docker build`／`compose up`／區網測試）仍建議在乾淨環境執行。

---

## 檔案結構（將建立或修改）

| 檔案 | 職責 |
|------|------|
| `backend/Dockerfile` | 安裝系統依賴（rembg / onnxruntime 常需 `libgomp1` 等）、`pip install -r requirements.txt`、建立 `appuser`、透過 entrypoint 以非 root 執行 uvicorn 於 `0.0.0.0:8000`。 |
| `backend/docker-entrypoint.sh` | 以 root 啟動時將 `$STORAGE_ROOT` `chown` 給 `appuser` 後降權執行 CMD（支援具名 volume 掛載）。 |
| `frontend/nginx.docker.conf` | Nginx：`/` 靜態檔、`/api/` 與 `/health` 轉發後端；上傳大小與逾時對齊產品行為；容器內監聽非特權埠（8080）。 |
| `frontend/Dockerfile` | 多階段：Node `npm ci` + `npm run build`；第二階段 `nginxinc/nginx-unprivileged` 提供 `dist` + 上述設定。 |
| `docker-compose.yml`（repo 根目錄） | 定義 `backend`、`web`、內部網路、`web` 的埠映射、後端 healthcheck、選用 volume 持久化 `STORAGE_ROOT`。 |
| `README.md` | 新增「Docker（區網）」小節：指令、埠、防火牆、與 Zeabur 文件分工。 |

---

### Task 1: 後端 `backend/Dockerfile`

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/docker-entrypoint.sh`（啟動時將 `$STORAGE_ROOT` 擁有者調整為 `appuser`，再以非 root 執行 uvicorn）

- [x] **Step 1: 新增 `backend/Dockerfile`（完整內容如下）**

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
  && rm -rf /var/lib/apt/lists/*

RUN groupadd --system appuser \
  && useradd --system --gid appuser --no-create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN chown -R appuser:appuser /app

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV STORAGE_ROOT=/data/storage
RUN mkdir -p /data/storage

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [x] **Step 2: 僅建置後端映像以驗證 Dockerfile**

Run（於 repo 根目錄）:

```bash
docker build -t life-course-rembg-backend:test ./backend
```

Expected: 建置成功結束（exit code 0）。若 `pip` 或 `rembg` 於建置階段報缺少共享函式庫，將錯誤訊息對照 Debian 套件名補進 `apt-get install` 列後再重試。

- [x] **Step 3: 以一次性容器 smoke 測試 `/health`（模型載入較慢，逾時可酌調）**

Run:

```bash
docker run --rm -d --name rembg-health-test -p 18000:8000 life-course-rembg-backend:test
sleep 90
curl -sS "http://127.0.0.1:18000/health"
docker stop rembg-health-test
```

Expected: HTTP **200** 時 `curl` 回傳 JSON，形狀與 `GET /health` 一致，例如含 `"status":"ok"` 與 `"checks":{"rembg":true}`（見 `backend/app/main.py`）。啟動完成前連線可能失敗或逾時；若 90 秒內尚未就緒，延長 `sleep` 後重試；若始終失敗，檢視 `docker logs rembg-health-test`。

- [x] **Step 4: Commit**

```bash
git add backend/Dockerfile
git commit -m "chore(docker): add backend image for FastAPI and rembg"
```

---

### Task 2: 前端 Nginx 設定 `frontend/nginx.docker.conf`

**Files:**
- Create: `frontend/nginx.docker.conf`

- [x] **Step 1: 新增 `frontend/nginx.docker.conf`（完整內容如下）**

```nginx
server {
  listen 8080;
  server_name _;

  root /usr/share/nginx/html;
  index index.html;

  client_max_body_size 10m;

  # proxy_read_timeout／proxy_send_timeout 須大於 REMOVE_BG_TIMEOUT（見倉庫內 frontend/nginx.docker.conf 註解）

  location = /health {
    proxy_pass http://backend:8000/health;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 10s;
    proxy_read_timeout 300s;
  }

  location /api/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 10s;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
  }

  location / {
    try_files $uri $uri/ /index.html;
  }
}
```

說明（實作者無需改檔）：`proxy_pass http://backend:8000` 不帶路徑前綴，會把完整 URI（例如 `/api/remove-background`）轉到後端，與本機 Vite `proxy['/api'].target` 行為一致。

- [x] **Step 2: Commit**

```bash
git add frontend/nginx.docker.conf
git commit -m "chore(docker): add nginx config for LAN single-origin proxy"
```

---

### Task 3: 前端多階段映像 `frontend/Dockerfile`

**Files:**
- Create: `frontend/Dockerfile`

- [x] **Step 1: 新增 `frontend/Dockerfile`（完整內容如下）**

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.docker.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
```

- [x] **Step 2: 單獨建置前端映像（此時 Nginx 上游 `backend` 尚不存在，僅驗證 build 與靜態檔層）**

Run:

```bash
docker build -t life-course-rembg-web:test ./frontend
```

Expected: 建置成功結束（exit code 0）。

- [x] **Step 3: Commit**

```bash
git add frontend/Dockerfile
git commit -m "chore(docker): add multi-stage web image with nginx"
```

---

### Task 4: `docker-compose.yml`（根目錄）

**Files:**
- Create: `docker-compose.yml`

- [x] **Step 1: 於 repo 根目錄新增 `docker-compose.yml`（完整內容如下）**

```yaml
services:
  backend:
    build: ./backend
    restart: unless-stopped
    environment:
      DOCS_ENABLED: "false"
      STORAGE_ROOT: /data/storage
    volumes:
      - backend_storage:/data/storage
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()",
        ]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 180s

  web:
    build: ./frontend
    ports:
      - "8080:8080"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

volumes:
  backend_storage: {}
```

說明：`8080:8080` 將主機 8080 對應到容器內 Nginx 監聽的 **8080**（`nginxinc/nginx-unprivileged` 非特權埠）；避免在 Windows 上占用主機 80 埠常見的權限問題。若要以主機 80 對外，改為 `"80:8080"` 並確保作業系統允許綁定。`start_period` 與 `retries` 預留 rembg 模型載入時間。

- [x] **Step 2: 啟動堆疊並檢查容器狀態**

Run（於 repo 根目錄）:

```bash
docker compose up -d --build
docker compose ps
```

Expected: `backend` 狀態最終為 `healthy`（或 `running` 且 healthcheck 通過），`web` 為 `running`。

- [x] **Step 3: 本機驗證 Nginx 轉發 `/health`**

Run:

```bash
curl -sS "http://127.0.0.1:8080/health"
```

Expected: 與直接打後端時相同結構的 JSON（例如 `status`、`checks`，見 `backend/app/main.py` 的 `GET /health`）。

- [x] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "chore(docker): add compose stack for backend and web proxy"
```

---

### Task 5: 更新 `README.md`（Docker 區網一節）

**Files:**
- Modify: `README.md`（在「雲端部署（Zeabur）」一節之後或適當位置插入小節）

- [x] **Step 1: 插入下列 Markdown 段落（可依文件語氣微調用字，但指令與埠號需保留）**

````markdown
## Docker（區網／Windows 主機）

- **目的**：在本機 Docker 上以**單一 HTTP 埠**同時提供前端與 API（Nginx 反向代理），方便同一 Wi‑Fi 下的手機或其他電腦連線。
- **前置**：已安裝 Docker Desktop（Windows 建議啟用 WSL2 後端）。
- **啟動**（repo 根目錄）：

```bash
docker compose up -d --build
```

- **本機瀏覽**：`http://localhost:8080/`（若將 compose 埠改為 `80:80`，則為 `http://localhost/`）。
- **區網裝置**：在 Windows 以 `ipconfig` 查 IPv4，於手機／其他電腦開 `http://<該IPv4>:8080/`。
- **防火牆**：視需要允許 **TCP 8080**（或你映射的埠）於「私人網路」連入。
- **前端 API 基底網址**：與 Zeabur 不同，此模式**不必**設定 `VITE_API_BASE_URL`（未設定時前端使用相對路徑 `/api/...`）。
- **處理逾時**：後端 `REMOVE_BG_TIMEOUT` 與 Nginx `proxy_read_timeout`／`proxy_send_timeout` 必須一併考量（見 README 與 `frontend/nginx.docker.conf` 註解）。
- **與 Zeabur 文件分工**：雲端雙服務部署仍見 `docs/plans/2026-04-08-zeabur-deploy-checklist.md`。
````

- [x] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document Docker Compose LAN usage on Windows"
```

---

### Task 6: 端到端驗收（本機 + 區網）

**Files:**
- （無強制新增檔案；若你希望 CI 可重跑，可另開議題加入最小 smoke script）

- [x] **Step 1: 本機瀏覽器開啟應用並完成去背流程**

手動：開啟 `http://localhost:8080/`，上傳一張允許格式且小於 10 MB 的圖片，確認可下載去背 PNG。

- [x] **Step 2: 區網第二裝置**

手動：同一 Wi‑Fi 下以 `http://<Windows區網IP>:8080/` 重複 Step 1。

- [x] **Step 3: 檢視日誌（故障排除用）**

Run:

```bash
docker compose logs --tail=100 web
docker compose logs --tail=100 backend
```

Expected: 無持續性錯誤；若 Nginx 出現 `upstream timed out`，先確認 `proxy_read_timeout`／`proxy_send_timeout` **大於** `REMOVE_BG_TIMEOUT` 並預留餘量，再視需要調高兩者後重建 `web` 映像並重測。

- [x] **Step 4: （選擇性）最終 commit**

若僅調整 README 以外的設定且已在前面任務提交，可略過；若有修正 compose 或 nginx，請單獨提交。

```bash
git status
# 若有變更：
git add -A
git commit -m "fix(docker): adjust timeouts or ports after LAN verification"
```

---

## 計畫自檢（對照 spec）

1. **Spec 涵蓋：** §1 雙服務與單一入口 → Task 4、Task 2；§2 多階段前端 + pip 後端 → Task 1、Task 3；§3 區網與防火牆 → Task 5、Task 6；§4 驗收與觀測 → Task 4 Step 3、Task 6。  
2. **占位掃描：** 無 `TBD`／空實作步驟；Nginx 與路由對齊已依原始碼定稿。  
3. **型別／介面一致：** 後端路由為 `/api/remove-background` 與 `/health`；前端空 `VITE_API_BASE_URL` 時為 `/api/remove-background`，與 Nginx `location /api/` 一致。

---

## 執行交接

**計畫已寫入：** `docs/superpowers/plans/2026-04-09-docker-lan-reverse-proxy.md`

**兩種執行方式：**

1. **Subagent-Driven（建議）** — 每個 Task 由新 subagent 執行，任務間由你 review，迭代較快。  
2. **Inline Execution** — 在本對話（或同一工作階段）依 `executing-plans` 批次執行並設檢查點。

**你要用哪一種？** 若無偏好，回覆「1」或「2」即可；若要我**直接在本工作樹開始實作**，回覆「開始實作」我會依 Task 順序修改檔案並跑驗證指令。
