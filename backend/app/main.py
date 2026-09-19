"""FastAPI application entry point. Creates tables, seeds sample data, serves API and frontend."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.routers import customers, dashboard, health, interactions
from app.seed import seed_if_empty
from app.services.ai.factory import get_providers

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_if_empty(session)
    judgment, generation = get_providers()
    log.info(
        "AI providers: judgment=%s generation=%s model=%s",
        judgment.name,
        generation.name,
        getattr(generation, "model", None),
    )
    yield


app = FastAPI(title="AI-Powered Micro-CRM", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (health.router, dashboard.router, customers.router, interactions.router):
    app.include_router(router)


def mount_frontend(application: FastAPI) -> None:
    """Serve the built React app (Docker/production). In development Vite serves it instead."""
    dist = Path(get_settings().frontend_dist).resolve()
    if not (dist / "index.html").exists():
        return
    application.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @application.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")


mount_frontend(app)
