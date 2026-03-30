# Standalone migration: Remove Background (FastAPI + rembg + React/Vite)

**Purpose:** 將「圖片去背」功能自本倉庫拆出為獨立專案（框架不變：FastAPI、rembg、React、Vite），並說明可行性、完整檔案清單、需手動刪改處與操作順序。

**Audience:** 執行拆倉的工程師（非僅複製貼上即可完成）。

**現況（`Life-Course-REMBG`）：** 來源檔案已複製；**§3.1–§3.10** 精簡已完成；**§5.1 後端**、**§5.2 前端**（`npm install`、`npm run dev`、瀏覽器呼叫去背）已驗；§4.5 主要項已勾選（見下表）。

**整併與驗證紀錄（對 `main`）：** 以 `main` 為基底另開分支 **`sync/main-fe`**，自 **`dev/rmb-migration`** 選取帶入 **`docs/MIGRATION_REMOVE_BACKGROUND_STANDALONE.md`** 與 **`frontend/`**（避免與 `main` 直接 merge 造成大量衝突合併）。**後端沿用 `main`**，與本文件最初假設「測試集與後端同線自遷移分支」略有出入（例如 `backend/tests` 是否齊備、pytest 筆數可能與 §5.1 表格不同），但**實測**後 **`GET /health`**、**Vite dev + `/api` proxy**、**瀏覽器去背流程**均正常。**結論：** 自原專案拆出之 **standalone** 路線已與 **`main` 整併並驗證通過**（merge + smoke／§5 核心項目 OK）。

---

## 1. 可行性分析

### 1.1 結論：**可行**，但多數「邊界檔」無法原樣複製

| 面向 | 評估 |
|------|------|
| **技術** | 去背路徑邊界清楚：`POST /api/remove-background`、`images.py`、`rembg` 預載、`ImageUploader` + `removeBackground`。與語音／3D 無執行期耦合。 |
| **主要工時** | 在 **精簡共用檔**（`main.py`、`requirements.txt`、`conftest.py`、`App.jsx`、`index.css`、`package.json`、`test_health.py`、`test_docs_toggle.py`、`api.js`）與 **驗證測試／手動 smoke**；不是單純整包目錄複製。 |
| **風險** | 若漏刪 `main.py` 的 XTTS／torch 依賴，獨立專案仍會拉超重依賴或啟動失敗。若前端保留 `@google/model-viewer` 等僅 3D 用之依賴，則與「僅去背」目標不一致。 |
| **文件** | `PRD_v1.md`／`sdd_v1.md` 描述整個 API Gateway MVP，**不建議**整份當作獨立去背專案規格；宜節錄或改寫成單一功能 README／簡短 SPEC。 |

### 1.2 與「只搬一～三節所列檔案」的對應

先前整理之「一～三」包含 **共用模組** 與 **整檔含多功能的檔案**。搬移時應：

- **可直接沿用（或僅改 import 路徑／專案名）的**：`images.py`、`validation.py`（邏輯通用）、`config.py`、`ImageUploader.jsx`、多數 hooks／utils／UI 元件。
- **必須手動刪除非去背邏輯的**：`main.py`、`constants.py`（後端）、`requirements.txt`、`conftest.py`、`test_health.py`、`test_docs_toggle.py`、`App.jsx`、`api.js`、`package.json`、`index.css`（刪除語音／3D／Tab 樣式區塊）。

因此：**提議方向正確**，但實務上應視為「**以清單為基礎的搬移 + 必做精簡**」，而非「檔案級純複製即完成」。

---

## 2. 須遷移／納入獨立專案之檔案（完整清單）

路徑以本倉庫 `Life-Course-Remove-Background/` 為根。新專案目錄以下稱 **`NEW_REPO/`**（自訂名稱，例如 `remove-background-app`）。

### 2.1 後端（建議結構維持 `backend/app/...`）

| # | 來源路徑 | 備註 |
|---|----------|------|
| B1 | `backend/app/routes/images.py` | 去背路由本體；可原樣納入。 |
| B2 | `backend/app/validation.py` | 上傳驗證；可原樣納入（僅依賴 `constants` 之通用欄位）。 |
| B3 | `backend/app/config.py` | CORS、`DOCS_ENABLED`；可原樣納入。 |
| B4 | `backend/app/constants.py` | **須刪除非圖片常數後**再納入（見 §3）。 |
| B5 | `backend/app/main.py` | **須改寫**為僅 rembg + `images` router（見 §3）；不可原樣複製。 |
| B6 | `backend/requirements.txt` | **須刪減**依賴（見 §3）；不可原樣複製。 |
| B7 | `backend/tests/test_images.py` | 去背端點測試；納入後需與新 `conftest` 對齊。 |
| B8 | `backend/tests/conftest.py` | **須精簡** mock 清單（見 §3）；不可原樣複製。 |
| B9 | `backend/tests/test_health.py` | **須刪除** xtts 相關斷言與案例（見 §3）。 |
| B10 | `backend/tests/test_docs_toggle.py` | 可選；若保留，**須改**為以 `/api/remove-background` 驗證 API 仍可用（見 §3）。 |

**不搬移（與去背無關）：** `backend/app/routes/voice.py`、`backend/app/routes/threed.py`、`backend/tests/test_voice.py`、`backend/tests/test_threed.py`。

### 2.2 前端

| # | 來源路徑 | 備註 |
|---|----------|------|
| F1 | `frontend/src/components/ImageUploader.jsx` | 去背 UI；可原樣納入。 |
| F2 | `frontend/src/services/api.js` | **刪除** `convertTo3D`、`cloneVoice` 後納入；或僅保留 `postForBlob` + `removeBackground`。 |
| F3 | `frontend/src/constants.js` | 僅圖片限制；可原樣納入。 |
| F4 | `frontend/src/utils/validateImageFile.js` | 可原樣納入。 |
| F5 | `frontend/src/utils/revokeResultUrl.js` | 可原樣納入。 |
| F6 | `frontend/src/hooks/useAsyncSubmit.js` | 可原樣納入。 |
| F7 | `frontend/src/hooks/useObjectUrl.js` | 可原樣納入。 |
| F8 | `frontend/src/components/LoadingButton.jsx` | 可原樣納入。 |
| F9 | `frontend/src/components/ProgressStatus.jsx` | 可原樣納入。 |
| F10 | `frontend/src/App.jsx` | **改寫**為單一頁（無 Tab／無 Voice／3D）（見 §3）。 |
| F11 | `frontend/src/main.jsx` | 可原樣納入。 |
| F12 | `frontend/index.html` | 可原樣納入（可改 `<title>`）。 |
| F13 | `frontend/src/index.css` | **刪除** `.nav-tabs`、`.voice-cloner`、`model-viewer` 等區塊後納入；或只複製與 `.uploader`／表單／預覽相關規則。 |
| F14 | `frontend/vite.config.js` | 可原樣納入（`/api` proxy 不變）。 |
| F15 | `frontend/package.json` | **刪除** `@google/model-viewer` 依賴（見 §3）。 |
| F16 | `frontend/eslint.config.js` | 可原樣納入（若保留 ESLint）。 |

**不搬移：** `VoiceCloner.jsx`、`ImageTo3D.jsx`。

### 2.3 倉庫根與說明文件

| # | 來源路徑 | 備註 |
|---|----------|------|
| R1 | `.gitignore` | 可原樣或合併至新專案。 |
| R2 | `README.md` | **建議改寫**為僅描述去背與啟動方式；勿複製舊 README 中已過時之 JSON 成功格式若與現行程式不符（以 `images.py` 為準：PNG 二進位）。 |
| R3 | `docs/BACKEND_Conda_Setup.md` | 可選；內容與去背相關，可一併搬移並更新路徑／專案名。 |
| R4 | `docs/PHASE0_AS_IS.md` | 可選；若作為「單一功能基準」宜 **節錄** 去背／API 段落並修正與現行程式一致之敘述。 |
| R5 | `docs/phase0_test.md` | 可選；手動測試清單可節錄去背相關步驟。 |

**不建議整包原樣搬移（除非刻意保留歷史）：** `docs/PRD_v1.md`、`docs/sdd_v1.md`（範圍為整個 Gateway，易誤導獨立去背專案）。若需要，請另寫 **簡短 SPEC** 取代。

### 2.4 先前「一～三」類別對照（方便核對）

- **一、後端實作：** B1–B6（`main.py`、`constants.py` 需編輯）。
- **二、前端實作：** F1–F16（`App.jsx`、`api.js`、`index.css`、`package.json` 需編輯）。
- **三、文件：** R2–R5 為主；其餘 `docs/plans/`、`docs/brainstorms/` 屬歷史計畫，**非執行拆倉必要**，可選擇性不搬。

### 2.5 `Life-Course-REMBG/` 目錄與檔案一覽（Step 1：自來源複製完成後）

以下為獨立專案根目錄 **`Life-Course-REMBG/`**（與 §2 清單對齊；路徑相對於該根目錄）。**不含** `frontend/node_modules`（於 `frontend/` 執行 `npm install` 後產生）。**額外納入** `backend/app/__init__.py`、`backend/app/routes/__init__.py`（與來源一致，供套件匯入）。

```
Life-Course-REMBG/
├── .gitignore
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── validation.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── images.py
│   └── tests/
│       ├── conftest.py
│       ├── test_images.py
│       ├── test_health.py
│       └── test_docs_toggle.py
├── frontend/
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       ├── constants.js
│       ├── components/
│       │   ├── ErrorBoundary.jsx
│       │   ├── ImageUploader.jsx
│       │   ├── LoadingButton.jsx
│       │   └── ProgressStatus.jsx
│       ├── services/
│       │   └── api.js
│       ├── utils/
│       │   ├── validateImageFile.js
│       │   └── revokeResultUrl.js
│       └── hooks/
│           ├── useAsyncSubmit.js
│           └── useObjectUrl.js
└── docs/
    ├── MIGRATION_REMOVE_BACKGROUND_STANDALONE.md
    ├── BACKEND_Conda_Setup.md
    ├── PHASE0_AS_IS.md
    └── phase0_test.md
```

**刻意未複製（與去背無關）：** `VoiceCloner.jsx`、`ImageTo3D.jsx`、`backend/app/routes/voice.py`、`threed.py`、`test_voice.py`、`test_threed.py` 等。

**歷史說明（Step 1）：** 最初為自 `Life-Course-Remove-Background` **複製**之快照；後續已依 **§3** 在 `Life-Course-REMBG` 內完成精簡，與本節樹狀圖一致之結構下，程式內容已為「僅去背」版本（詳 §3.0）。

---

## 3. 需手動刪除或改寫「無關功能」的檔案

以下為 **同一檔案內** 必須處理的項目（按優先順序）。

### 3.0 進度總覽（`Life-Course-REMBG`）

| 節 | 說明 | 狀態 |
|:---:|------|:----:|
| §3.1 | `backend/app/main.py` | ✅ |
| §3.2 | `backend/app/constants.py` | ✅ |
| §3.3 | `backend/requirements.txt` | ✅ |
| §3.4 | `backend/tests/conftest.py` | ✅ |
| §3.5 | `backend/tests/test_health.py` | ✅ |
| §3.6 | `backend/tests/test_docs_toggle.py` | ✅ |
| §3.7 | `frontend/package.json` | ✅（含本機 `npm install`／lockfile 已更新） |
| §3.8 | `frontend/src/App.jsx` | ✅ |
| §3.9 | `frontend/src/services/api.js` | ✅ |
| §3.10 | `frontend/src/index.css` | ✅ |

### 3.1 `backend/app/main.py` ✅

**細步驟（已全部完成）：**

- [x] **3.1-A** — `lifespan` 內移除 XTTS 載入與 XTTS 相關 teardown，僅保留 rembg 載入與 `del app.state.rembg_session`。
- [x] **3.1-B** — 刪除 `COQUI_TOS_AGREED`、`torch`、`TTS`、`MAX_XTTS_PENDING` 與未使用之 `asyncio`／`os` import。
- [x] **3.1-C** — 刪除 `threed`／`voice` 之 `import` 與 `include_router`。
- [x] **3.1-D** — `/health` 之 `checks` 僅保留 `rembg`，移除 `xtts_v2`。

**對應原條文：**

- [x] 刪除：`COQUI_TOS_AGREED`、`torch`、`TTS` 相關 import 與 lifespan 內 XTTS 載入、`app.state.tts_model`、`xtts_lock`、`xtts_semaphore`。
- [x] 刪除：`from app.routes.threed import`、`from app.routes.voice import` 與對應 `include_router`。
- [x] 保留：`rembg` 的 `new_session`、lifespan 內 `app.state.rembg_session`、`images_router`、`CORSMiddleware`、安全標頭 middleware、`/health` 但僅檢查 `rembg`（見下）。
- [x] `/health` 回應改為僅 `checks.rembg`（或維持一物件但移除 `xtts_v2` 鍵），與 `test_health.py` 一致。

### 3.2 `backend/app/constants.py` ✅

**目標：** 刪除語音／3D 專用常數，只保留圖片去背與驗證所需。

**細步驟（已全部完成）：**

| 步驟 | 動作 |
|------|------|
| **3.2-A** | 刪除 `# Audio magic bytes` 註解，以及 `EBML_MAGIC`、`OGGS_MAGIC`、`FTYP_MAGIC`（三個語音／容器相關魔數）。 |
| **3.2-B** | 刪除 `# Voice route constants` 區塊：`MAX_PCM_SIZE`、`MAX_XTTS_PENDING`、`MIME_TO_FORMAT` 整段。 |
| **3.2-C** | 刪除 `ALLOWED_3D_MIME_TYPES`。若 `# Allowed MIME types per route` 下僅剩 `ALLOWED_IMAGE_MIME_TYPES`，可將註解改為例如「圖片上傳允許之 MIME」或保留原意簡短說明。 |
| **3.2-D**（可選） | 將模組 docstring `"""Shared constants used across route modules."""` 改為僅描述圖片／去背用途（例如 `"""Constants for image upload and validation."""`）。 |

- [x] **3.2-A** — 已刪除語音魔數區塊。
- [x] **3.2-B** — 已刪除 Voice route 常數與 `MIME_TO_FORMAT`。
- [x] **3.2-C** — 已刪除 `ALLOWED_3D_MIME_TYPES`，註解改為圖片上傳 MIME。
- [x] **3.2-D** — docstring 已改為 `Constants for image upload and validation`。

**摘要 checklist：**

- [x] 刪除：語音魔數、`MIME_TO_FORMAT`、`MAX_PCM_SIZE`、`MAX_XTTS_PENDING`、`ALLOWED_3D_MIME_TYPES`。
- [x] 保留：`MAX_FILE_SIZE`、`FILE_TOO_LARGE_DETAIL`、PNG／JPEG／WebP 魔數、`ALLOWED_IMAGE_MIME_TYPES`。

### 3.3 `backend/requirements.txt` ✅

- [x] **保留（去背 + 測試 + 執行服務）：** `fastapi`、`uvicorn`、`python-multipart`、`rembg[cpu]`、`pillow`、`httpx`、`pytest`、`pytest-asyncio`（版本對齊現有）。
- [x] **刪除：** `pydub`、`anyio`（明確 pin；`rembg`/FastAPI 會透過傳遞依賴帶入 `anyio`）、`coqui-tts`、`torch`、`torchaudio`。

### 3.4 `backend/tests/conftest.py` ✅

- [x] `_APP_MODULES` 僅列出：`app.main`、`app.config`、`app.routes.images`（已移除 `threed`、`voice`）。
- [x] 刪除 `_make_mock_tts_api`、`mock_torch`、`_make_standard_patches`（含 `torch`／`TTS` patch）；改為 **`_rembg_sys_modules_patch`**，僅 mock `rembg`**。`test_images.py` 已改為使用該 helper。
- [x] 刪除 `voice_mocks`、`mock_ffprobe` fixture。

### 3.5 `backend/tests/test_health.py` ✅

- [x] 刪除：`test_health_missing_tts` 整段。
- [x] 修改：`test_health_returns_ok`、`test_health_missing_rembg` 中對 `data["checks"]` 的斷言，移除 `xtts_v2`；並斷言 `checks` 僅含 `rembg` 鍵。

### 3.6 `backend/tests/test_docs_toggle.py`（若保留）✅

- [x] `test_api_still_works_when_docs_disabled` 改為對 `POST /api/remove-background` 上傳合法 PNG；`patch("app.routes.images.remove", ...)` 避免依賴真實 rembg；預期 `200`。
- [x] `_make_app` 改為僅使用 `_rembg_sys_modules_patch`（與 §3.4 一致）。

### 3.7 `frontend/package.json` ✅（manifest）

- [x] 自 `dependencies` **移除** `@google/model-viewer`。
- [x] 於 `frontend/` 執行 `npm install` 以更新 `package-lock.json`（與已移除之 `@google/model-viewer` 對齊）。

### 3.8 `frontend/src/App.jsx` ✅

- [x] 移除 Tab、`VoiceCloner`、`ImageTo3D` import 與 state（含 `TabPanel`、`useState`）。
- [x] 單一版面：標題「圖片去背」+ `<ImageUploader visible />`。

### 3.9 `frontend/src/services/api.js` ✅

- [x] 移除 `convertTo3D`、`cloneVoice` 函式。
- [x] 保留內部 `postForBlob` 與 `removeBackground` 匯出。

### 3.10 `frontend/src/index.css` ✅

- [x] 已刪除 Tab Navigation（`.nav-tabs`、`.nav-tab`）、`VoiceCloner` 相關區塊、`ImageTo3D`／`model-viewer`／`.model-viewer-card` 區塊。
- [x] 保留共用版面、`.uploader`／預覽／下載、`ProgressStatus` 等去背 UI 所需規則。

### 3.11 搬移精簡完成摘要（`Life-Course-REMBG`）

| 項目 | 狀態 |
|------|:----:|
| §2 檔案複製至本 repo | ✅ |
| §3.1–§3.10 程式／測試／前端精簡 | ✅ |
| `frontend/package-lock.json` 與 `npm install` | ✅ |
| §5.1 後端（pytest、`uvicorn`、`GET /health`） | ✅ |
| §5.2 前端與瀏覽器 E2E | ✅ |

**可選清理：** 來源曾複製之 `VoiceCloner.jsx`、`ImageTo3D.jsx` 若仍留在 `frontend/src/components/` 且未被引用，可刪檔減少混淆（非啟動必要條件）。

---

## 4. 搬移操作指引（有序步驟）

### 4.1 建立新專案骨架

1. 建立 `NEW_REPO/`，初始化 git（若需要）。
2. 建立目錄：`NEW_REPO/backend/app/routes/`、`NEW_REPO/backend/tests/`、`NEW_REPO/frontend/src/components/` 等，與上表一致。

### 4.2 後端

1. 複製 **B1–B3** 原檔；複製 **B4** 後依 §3.2 刪行。
2. 自現有 **B5** 複製為草稿，依 §3.1 改寫；確認僅 `include_router(images_router)`。
3. 複製 **B6** 後依 §3.3 刪減；於乾淨 venv 執行 `pip install -r requirements.txt` 與 `uvicorn app.main:app --reload --port 8000` 驗證啟動（首次 rembg 可能下載模型）。
4. 複製 **B7–B10**，依 §3.4–§3.6 調整；執行 `pytest backend/tests -q`（於 `backend/` 下或設定 `PYTHONPATH`）。

### 4.3 前端

1. 複製 **F1–F9、F11–F14、F16**；複製 **F10、F2、F13、F15** 後依 §3.7–§3.10 修改。
2. 在 `frontend/` 執行 `npm install`、`npm run dev`，確認可呼叫去背 API 並預覽結果。
3. 執行 `npm run lint`（若有）。

### 4.4 文件與收尾

1. 撰寫或裁剪 **README**（啟動步驟、環境變數 `CORS_ALLOWED_ORIGINS`、`POST /api/remove-background`、10MB／格式限制）。
2. 選擇性加入 **R3–R5** 節錄版。
3. 於原倉庫（若仍繼續維護）決定是否 **刪除已遷移之去背專用檔案** 或 **保留雙線維護**；若刪除，需另開任務處理剩餘 Tab／路由之相依與測試。

### 4.5 驗收清單（建議）

- [x] `GET /health` 僅反映 rembg，且模型載入後為 200。（**§5.1 已驗**）
- [x] `POST /api/remove-background`：合法圖 → `200`、`image/png`；過大 → `413`；錯誤型別 → `415`。（**pytest** 覆蓋驗證案例；**§5.2** 手動多次 `POST` 回 **200 OK**）
- [x] 前端：選圖 → 去背結果預覽與下載正常；無 CORS 錯誤（與 `CORS_ALLOWED_ORIGINS` 一致）。（**§5.2 已驗**；預設 `localhost:5173`）
- [x] `pytest` 全綠（在精簡後的測試集下）。（**14 passed**，§5.1）
- [x] 新專案 `requirements.txt` 不含 `torch`／`coqui-tts`（除非刻意保留）。

---

## 5. 驗證與啟動（`Life-Course-REMBG`）

於 **§3 已完成** 後，在本機確認可運行。建議順序：**後端依賴與測試 → 啟動後端 → 前端依賴與啟動 → 瀏覽器 E2E**。

### 5.1 後端

0. 環境建立（範例：Conda）
   - `conda create --name Life-Course-REMBG python=3.11`
   - `conda activate Life-Course-REMBG`
   - `cd` 至專案目錄後 `cd backend`
1. 在 **`backend/`** 安裝依賴：
   - `python -m pip install -r requirements.txt`
(2.) 執行測試（工作目錄為 `backend/`，使 `app` 可匯入）：(此版本暫無測試腳本)
   - `python -m pytest tests -q`
3. 啟動 API：
   - `uvicorn app.main:app --reload --port 8000`
4. 檢查：`GET http://localhost:8000/health` → `200`，`checks` 僅含 `rembg`；首次實際去背請求可能觸發 rembg 模型下載，屬正常。

**§5.1 驗證完成紀錄（本機）**

| 項目 | 結果 |
|------|------|
| 環境 | Conda `Life-Course-REMBG`（Python 3.11），於 `backend/` 安裝 `requirements.txt` |
| `python -m pytest tests -q` | **14 passed**（可能有 `pytest-asyncio` 之 `asyncio_default_fixture_loop_scope` 提示，不影響通過） |
| `uvicorn app.main:app --reload --port 8000` | 啟動成功；日誌顯示 `Application startup complete.` |
| `GET /health` | **200**，本體約為 `{"status":"ok","checks":{"rembg":true}}` |
| 備註 | `GET /`、`GET /healthy` 若 **404** 屬預期（未實作根路徑；健康檢查路徑為 **`/health`**） |

### 5.2 前端

1. 在 **`frontend/`**：
   - `npm install`（更新 `package-lock.json` 與 `node_modules`，與已移除之 `@google/model-viewer` 對齊）
   - `npm run dev`（預設常為 `http://localhost:5173`，並將 `/api` proxy 至 `8000`）
2. 確認 **後端已先於 8000 埠運行**，否則 proxy 會失敗。
3. 若前端 origin 非預設，設定環境變數 **`CORS_ALLOWED_ORIGINS`**（後端）為實際 origin。

**§5.2 驗證完成紀錄（本機）**

| 項目 | 結果 |
|------|------|
| `npm install` | 成功；`package-lock.json` 已與現行 `package.json` 對齊 |
| `npm run dev`（Vite 8） | **ready**，`Local: http://localhost:5173/`；首次可出現 dependency pre-bundle 訊息，屬正常 |
| 瀏覽器 → 後端 | `POST /api/remove-background` 多筆 **200 OK**（uvicorn 日誌） |
| 補件（若曾報錯） | 已自 **`main.jsx` 移除** `import '@google/model-viewer'`；並補 **`components/ErrorBoundary.jsx`**（與 `main.jsx` 引用一致） |

### 5.3 Shell 注意（Windows）

- **PowerShell** 不支援 `cmd` 的 `cd /d` 與 **`&&`** 串接；請改為分號 `;` 或分行執行，例如：  
  `Set-Location path\to\backend; python -m pytest tests -q`

### 5.4 與 §4.5 的對應

§5 為 **操作步驟**；§4.5 為 **結果勾選**。兩者搭配使用即可記錄驗收完成度。

---

## 6. 附錄：不屬於「必搬」但可參考之路徑

若需追溯歷史設計，可從本倉庫查閱（不必複製進新 repo）：

- `docs/plans/2026-03-27-003-model-preload-plan.md`（rembg 預載）
- `docs/plans/2026-03-24-001-fix-stream-image-remove-disk-writes-plan.md`（串流回應）
- `docs/brainstorms/2026-03-24-output-disk-leak-requirements.md`

---

**Document version:** 2026-03-30 — §3 搬移精簡已完成；**§5.1–§5.2 本機驗證已完成**（pytest、`/health`、Vite、POST 去背 200；`main.jsx` 無 `model-viewer`、`ErrorBoundary.jsx` 已納入）。**2026-03-30 補：** `sync/main-fe` → `main` 整併紀錄已寫於開頭「**整併與驗證紀錄**」；後端以 `main` 為準時與下文 §5 測試矩陣可能略有出入，以實測為準。更新本行時請同步檢查開頭「現況」、整併紀錄、§3.11、§4.5、§5.2，避免與表格矛盾。  
**Related snapshot repo:** `Life-Course-Remove-Background`（來源）；獨立專案：`Life-Course-REMBG`
