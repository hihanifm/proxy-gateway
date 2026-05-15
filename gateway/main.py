from __future__ import annotations

import asyncio
import contextlib
import logging

import httpx
from fastapi import FastAPI

from gateway.adapters.registry import get_adapter
from gateway.config import settings
from gateway.middleware import StatsMiddleware
from gateway.routes import admin, chat, dashboard, health, models, stats as stats_route
from gateway.stats import stats

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def health_check_loop() -> None:
    url = settings.BACKEND_BASE_URL.rstrip("/") + settings.BACKEND_HEALTH_PATH
    last_status = None
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            try:
                r = await client.get(url)
                status = "healthy" if r.status_code < 400 else "degraded"
                error = None if r.status_code < 400 else f"HTTP {r.status_code}"
            except Exception as exc:
                status, error = "unhealthy", str(exc)

            await stats.update_health(status, error)
            if status != last_status:
                if error:
                    logger.warning("backend health changed %s → %s (%s)", last_status, status, error)
                else:
                    logger.info("backend health changed %s → %s", last_status, status)
                last_status = status
            await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL_S)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.adapter = get_adapter()
    logger.info("adapter loaded name=%s", settings.GATEWAY_ADAPTER)
    app.state.adapter_name = settings.GATEWAY_ADAPTER
    app.state.adapter_backend_url = (
        settings.OPENAI_BASE_URL if settings.GATEWAY_ADAPTER == "openai"
        else settings.BACKEND_BASE_URL if settings.GATEWAY_ADAPTER == "internal"
        else None
    )
    task = asyncio.create_task(health_check_loop())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


def create_app() -> FastAPI:
    app = FastAPI(title="LLM Proxy Gateway", lifespan=lifespan)
    app.add_middleware(StatsMiddleware)
    app.include_router(chat.router)
    app.include_router(models.router)
    app.include_router(stats_route.router)
    app.include_router(admin.router)
    app.include_router(dashboard.router)
    app.include_router(health.router)
    return app


app = create_app()
