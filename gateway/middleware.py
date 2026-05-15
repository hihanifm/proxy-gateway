import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from gateway.stats import stats

_TRACKED_PATH = "/v1/chat/completions"


class StatsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path != _TRACKED_PATH:
            return await call_next(request)

        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        await stats.request_started(client_ip)
        start = time.monotonic()
        try:
            return await call_next(request)
        finally:
            await stats.request_finished(time.monotonic() - start)
