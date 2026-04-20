from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import new_session

from app.config import get_cors_allowed_origins, get_storage_root, is_docs_enabled
from app.routes.images import router as images_router

logger = logging.getLogger(__name__)

_DOCS_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    start = time.monotonic()
    app.state.rembg_session = await loop.run_in_executor(None, new_session)
    elapsed = time.monotonic() - start
    app.state.model_load_seconds = round(elapsed, 1)
    logger.info("rembg model loaded in %.1fs", elapsed)

    yield

    del app.state.rembg_session
    del app.state.model_load_seconds
    logger.info("Models unloaded")


_docs_enabled = is_docs_enabled()
app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if _docs_enabled and request.url.path in _DOCS_PATHS:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "frame-ancestors 'none'"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


app.include_router(images_router)


@app.get("/health")
async def health() -> JSONResponse:
    storage_ok = True
    try:
        root = get_storage_root()
        tmp = root / ".health_check"
        tmp.write_text("ok")
        tmp.unlink()
    except Exception:
        storage_ok = False
        logger.warning("Storage writable check failed for %s", root)

    checks = {
        "rembg": getattr(app.state, "rembg_session", None) is not None,
        "storage_writable": storage_ok,
    }
    healthy = all(checks.values())
    content = {"status": "ok" if healthy else "loading", "checks": checks}
    load_time = getattr(app.state, "model_load_seconds", None)
    if load_time is not None:
        content["model_loaded_in_s"] = load_time
    return JSONResponse(
        status_code=200 if healthy else 503,
        content=content,
    )
