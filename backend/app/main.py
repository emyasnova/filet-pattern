"""FastAPI application entrypoint."""

from collections import defaultdict, deque
from pathlib import Path
from time import monotonic

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import Settings, get_settings

PUBLIC_READ_PATHS = {"/api/v1/patterns", "/api/v1/categories", "/api/v1/tags"}
RESERVED_PREFIXES = ("/api/", "/docs", "/openapi.json", "/redoc", "/health", "/ready")


class ProductionMiddleware(BaseHTTPMiddleware):
    """Apply canonical-host, rate-limit, and browser security policy."""

    def __init__(self, app: FastAPI, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        host = request.url.hostname or ""
        canonical = self.settings.canonical_host
        if canonical and host == f"www.{canonical}":
            target = request.url.replace(netloc=canonical)
            return self._secure(RedirectResponse(str(target), status_code=308))

        if request.method == "GET" and request.url.path in PUBLIC_READ_PATHS:
            now = monotonic()
            key = request.client.host if request.client else "unknown"
            bucket = self.requests[key]
            while bucket and bucket[0] < now - 60:
                bucket.popleft()
            if len(bucket) >= self.settings.public_read_rate_limit:
                return self._secure(
                    JSONResponse({"detail": "Too many requests"}, status_code=429)
                )
            bucket.append(now)

        response = await call_next(request)
        return self._secure(response)

    @staticmethod
    def _secure(response: Response) -> Response:
        """Attach browser security headers to every middleware response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'none'"
        )
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the API and optional compiled frontend."""
    runtime_settings = settings or get_settings()
    app = FastAPI(title="Filet Pattern Backend", version="0.1.0")
    app.dependency_overrides[get_settings] = lambda: runtime_settings
    app.add_middleware(ProductionMiddleware, settings=runtime_settings)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=runtime_settings.allowed_hosts)
    app.include_router(api_router)

    dist = Path(runtime_settings.frontend_dist_dir)
    index = dist / "index.html"
    assets = dist / "assets"
    if index.is_file() and assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

        @app.get("/{client_path:path}", include_in_schema=False)
        def frontend(client_path: str) -> FileResponse:
            """Serve the Vite entrypoint for root and client-side routes."""
            path = f"/{client_path}"
            if path.startswith(RESERVED_PREFIXES):
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            return FileResponse(index)

    return app


app = create_app()
