from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # place for warm-up / background workers in later phases
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Careero API",
        version="0.1.0",
        description=(
            "Careero is a PersonaArmory product — Your AI Career Intelligence "
            "Platform. This is the backend API surface."
        ),
        lifespan=lifespan,
    )

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
        return {"name": "Careero API", "docs": "/docs"}

    return app


app = create_app()
