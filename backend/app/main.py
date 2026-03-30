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

from app.config import get_cors_allowed_origins, is_docs_enabled
from app.routes.images import router as images_router

logger = logging.getLogger(__name__)

_DOCS_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    start = time.monotonic()
    app.state.rembg_session = await loop.run_in_executor(None, new_session)
    elapsed = time.monotonic() - start
    logger.info("rembg model loaded in %.1fs", elapsed)

    yield

    del app.state.rembg_session
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
    checks = {
        "rembg": getattr(app.state, "rembg_session", None) is not None,
    }
    healthy = all(checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ok" if healthy else "loading", "checks": checks},
    )
