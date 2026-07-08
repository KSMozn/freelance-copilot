from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # place for warm-up / background workers in later phases
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    # Interactive API docs enumerate every route (incl. the task endpoint) and
    # the full schema — keep them off in production.
    docs_enabled = settings.environment != "production"
    app = FastAPI(
        title="Careero API",
        version="0.1.0",
        description=(
            "Careero is a PersonaArmory product — Your AI Career Intelligence "
            "Platform. This is the backend API surface."
        ),
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    is_deployed = settings.environment in ("staging", "production")

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        # CSP here only guards this JSON API; the SPA/admin ship their own via
        # nginx. frame-ancestors 'none' backstops X-Frame-Options for the
        # clients that honour CSP. No script/style rules so /docs still loads.
        response.headers.setdefault("Content-Security-Policy", "frame-ancestors 'none'")
        if is_deployed:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains",
            )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        body = {"name": "Careero API"}
        if docs_enabled:
            body["docs"] = "/docs"
        return body

    return app


app = create_app()
