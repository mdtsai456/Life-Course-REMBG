---
date: 2026-03-30
topic: rembg-backend-rewrite
---

# Remove BG Backend Rewrite

## Problem Frame

The original `Life-Course-Remove-Background-main` backend bundles three features (Remove BG, Voice Clone, Image-to-3D) into one codebase with heavy dependencies (torch, coqui-tts, pydub). The user wants a clean, focused Remove BG backend in the berlin workspace, free of unrelated code and dependencies. Backend first, frontend will follow in a separate effort.

## Requirements

**Core API**
- R1. Provide a `POST /api/remove-background` endpoint that accepts an image upload and returns a PNG with the background removed
- R2. Support PNG, JPEG, and WebP input formats, validated by magic bytes (not MIME type alone)
- R3. Enforce a 10 MB max file size with a 413 response when exceeded
- R4. Return 415 for unsupported file types

**App Infrastructure**
- R5. Use FastAPI with lifespan-based rembg session management (preload model at startup)
- R6. Include CORS middleware with configurable allowed origins via `CORS_ALLOWED_ORIGINS` env var
- R7. Include security headers middleware (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, CSP)
- R8. Provide a `GET /health` endpoint that reports rembg readiness
- R9. Support configurable Swagger docs via `DOCS_ENABLED` env var

## Success Criteria

- The backend starts, loads the rembg model, and responds to `/health` with `{"status": "ok"}`
- Uploading a valid image to `/api/remove-background` returns a PNG with transparent background
- Invalid files are rejected with appropriate error codes (413, 415)
- No Voice Clone or Image-to-3D dependencies are present

## Scope Boundaries

- No frontend (will be a separate effort)
- No Voice Clone or Image-to-3D features
- No Docker/deployment config (keep it simple for now)
- No tests in this first pass (can add later)

## Key Decisions

- **Tech stack**: Continue with FastAPI + rembg (same as original)
- **Migration approach**: Clean rewrite referencing original logic (not copy-paste)
- **Order**: Backend first, frontend later
- **Environment**: Use Python venv to avoid polluting local environment

## Next Steps

→ `/ce:plan` for structured implementation planning
