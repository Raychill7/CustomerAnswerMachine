from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.ticket import router as ticket_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.repositories import init_db
from app.middleware.metrics import MetricsMiddleware
from app.observability.metrics import render_metrics

settings = get_settings()
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(MetricsMiddleware)
allowed_origins = [item.strip() for item in settings.cors_allow_origins.split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(ticket_router)


@app.get("/metrics", tags=["ops"])
async def metrics() -> Response:
    return Response(content=render_metrics(), media_type="text/plain; version=0.0.4")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    web_file = Path("app/web/index.html")
    return FileResponse(web_file)
