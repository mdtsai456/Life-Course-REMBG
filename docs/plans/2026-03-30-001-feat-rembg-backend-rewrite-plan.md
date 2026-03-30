---
title: "feat: Rewrite Remove BG backend in berlin workspace"
type: feat
status: draft
date: 2026-03-30
origin: docs/brainstorms/2026-03-30-rembg-backend-rewrite-requirements.md
---

# feat: Rewrite Remove BG backend in berlin workspace

## Overview

Clean rewrite of the Remove BG backend from `Life-Course-Remove-Background-main` into the berlin workspace. Only the background removal feature is in scope — Voice Clone and Image-to-3D are excluded. Uses a Python venv to avoid polluting the local environment.

## Problem Frame

The original backend bundles three features (Remove BG, Voice Clone, Image-to-3D) with heavy dependencies (torch, coqui-tts). The user wants a focused, clean Remove BG backend free of unrelated code and dependencies.

## Requirements Trace

- R1. `POST /api/remove-background` — accepts image upload, returns PNG with background removed
- R2. Support PNG, JPEG, WebP validated by magic bytes
- R3. 10 MB max file size → 413
- R4. Unsupported file type → 415
- R5. FastAPI with lifespan-based rembg session (preload at startup)
- R6. CORS middleware via `CORS_ALLOWED_ORIGINS` env var
- R7. Security headers middleware (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, CSP)
- R8. `GET /health` reports rembg readiness
- R9. Configurable Swagger docs via `DOCS_ENABLED` env var

## Scope Boundaries

- No frontend (separate effort)
- No Voice Clone or Image-to-3D
- No Docker/deployment config
- No tests in this first pass

## Context & Research

### Relevant Code and Patterns

Original backend at `backend/app/`:
- `main.py` — app setup, lifespan, middleware, health check
- `config.py` — env-based config as plain functions
- `constants.py` — centralized constants with `frozenset` for MIME sets
- `validation.py` — generic `read_and_validate_upload()` with detector callback
- `routes/images.py` — remove-background endpoint with executor offload

### Patterns to Follow

1. `from __future__ import annotations` as first import in every file
2. Traditional Chinese (zh-TW) error messages in HTTP responses
3. Constants use `frozenset` for MIME type sets, `UPPER_SNAKE` naming
4. Config as plain functions reading `os.getenv()` with defaults
5. Route pattern: MIME hint log → validate via shared helper → check model readiness → executor offload → binary Response
6. `getattr(request.app.state, "...", None)` for safe model availability check
7. Private helpers prefixed with `_underscore`
8. Error codes: 413 (too large), 415 (bad type), 500 (processing failure with `from None`), 503 (model not ready)

## Key Technical Decisions

- **Venv isolation**: Use `python3 -m venv .venv` to avoid polluting local Python environment. User explicitly requested this.
- **Minimal dependencies**: Only fastapi, uvicorn, python-multipart, rembg, pillow. No torch/coqui-tts/pydub.
- **Same validation pattern**: Reuse the generic `read_and_validate_upload()` design — it's clean and extensible.
- **No test code this pass**: User wants to go slowly; tests can be added in a follow-up.

## Open Questions

### Resolved During Planning

- **Tech stack?** FastAPI + rembg (same as original, user confirmed)
- **Migration approach?** Clean rewrite referencing original logic (user chose this over copy-paste)
- **Scope?** Remove BG only, backend first (user confirmed)

### Deferred to Implementation

- **rembg version pinning**: Check latest stable version when writing requirements.txt
- **Python version minimum**: Original uses 3.11+; verify compatibility

## Implementation Units

- [ ] **Unit 1: Project scaffolding and venv**

  **Goal:** Create the directory structure, .gitignore, and Python virtual environment

  **Requirements:** Foundation for all other units

  **Dependencies:** None

  **Files:**
  - Create: `backend/app/__init__.py`
  - Create: `backend/app/routes/__init__.py`
  - Create: `backend/requirements.txt`
  - Create: `.gitignore`

  **Approach:**
  - Create directory tree: `backend/app/routes/`
  - Write `.gitignore` covering `.venv/`, `__pycache__/`, `*.pyc`
  - Write `requirements.txt` with only: fastapi, uvicorn[standard], python-multipart, rembg, pillow
  - Create and activate venv: `python3 -m venv backend/.venv`
  - Install dependencies inside venv
  - Empty `__init__.py` files for packages

  **Test expectation:** none — pure scaffolding

  **Verification:**
  - `backend/.venv/bin/python -c "import fastapi, rembg; print('ok')"` succeeds
  - No torch or TTS packages installed

- [ ] **Unit 2: Config and constants**

  **Goal:** Write the configuration and constants modules

  **Requirements:** R3, R6, R9

  **Dependencies:** Unit 1

  **Files:**
  - Create: `backend/app/config.py`
  - Create: `backend/app/constants.py`

  **Approach:**
  - `config.py`: Two plain functions — `get_cors_allowed_origins()` (default `http://localhost:5173`) and `is_docs_enabled()` (default `true`)
  - `constants.py`: Only image-related constants — `MAX_FILE_SIZE` (10 MB), magic bytes (PNG, JPEG, WebP), `FILE_TOO_LARGE_DETAIL` (zh-TW), `ALLOWED_IMAGE_MIME_TYPES` as `frozenset`
  - Follow original naming conventions exactly

  **Patterns to follow:**
  - Original `config.py` and `constants.py`

  **Test expectation:** none — pure configuration values

  **Verification:**
  - Module imports cleanly without errors
  - No audio/voice/3D constants present

- [ ] **Unit 3: Upload validation helper**

  **Goal:** Write the shared upload validation function

  **Requirements:** R2, R3, R4

  **Dependencies:** Unit 2

  **Files:**
  - Create: `backend/app/validation.py`

  **Approach:**
  - Implement `read_and_validate_upload()` following the original's generic callback pattern
  - Double-gated size check: header-based pre-check then actual read
  - Type detection via caller-provided `detect_type` callback
  - Return `(contents, detected_type)` tuple

  **Patterns to follow:**
  - Original `validation.py` — same function signature and logic flow

  **Test expectation:** none — tests deferred per scope

  **Verification:**
  - Module imports cleanly
  - Function signature matches the generic callback pattern

- [ ] **Unit 4: Images route**

  **Goal:** Write the remove-background API endpoint

  **Requirements:** R1, R2, R4

  **Dependencies:** Unit 2, Unit 3

  **Files:**
  - Create: `backend/app/routes/images.py`

  **Approach:**
  - Private `_detect_image_type()` using magic bytes for PNG/JPEG/WebP
  - `POST /api/remove-background`: validate upload → check rembg session → run `rembg.remove()` in executor → return PNG response
  - zh-TW error messages for 415/500/503 responses
  - Use `partial(remove, contents, session=session)` in `run_in_executor`

  **Patterns to follow:**
  - Original `routes/images.py` — same endpoint structure and error handling

  **Test expectation:** none — tests deferred per scope

  **Verification:**
  - Module imports cleanly
  - Router has one POST route at `/api/remove-background`

- [ ] **Unit 5: Main app entry point**

  **Goal:** Wire everything together — lifespan, middleware, routes, health check

  **Requirements:** R5, R6, R7, R8, R9

  **Dependencies:** Unit 2, Unit 4

  **Files:**
  - Create: `backend/app/main.py`

  **Approach:**
  - Lifespan: only load `rembg.new_session()` into `app.state.rembg_session` (no TTS)
  - CORS middleware using `get_cors_allowed_origins()`
  - Security headers middleware (same 4 headers as original)
  - `GET /health` checking rembg readiness
  - Include `images_router`
  - Swagger docs gated by `is_docs_enabled()`

  **Patterns to follow:**
  - Original `main.py` — same middleware and lifespan structure, minus TTS/voice/3D

  **Test expectation:** none — tests deferred per scope

  **Verification:**
  - App starts with `uvicorn app.main:app`
  - `GET /health` returns `{"status":"ok","checks":{"rembg":true}}`
  - `POST /api/remove-background` with a valid image returns a PNG
  - No torch/TTS/coqui imports anywhere in the codebase

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| rembg may pull in heavy dependencies (onnxruntime) | Expected — this is necessary for the feature to work |
| Model download on first run may be slow | Document in README or note to user |

## Sources & References

- **Origin document:** [docs/brainstorms/2026-03-30-rembg-backend-rewrite-requirements.md](../brainstorms/2026-03-30-rembg-backend-rewrite-requirements.md)
- Original backend: `backend/app/`
- rembg library: used for background removal via `new_session()` and `remove()`
