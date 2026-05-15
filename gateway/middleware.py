import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from gateway.stats import stats

logger = logging.getLogger(__name__)

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
        logger.info("request started ip=%s path=%s", client_ip, request.url.path)
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        except Exception:
            logger.warning("request error ip=%s path=%s", client_ip, request.url.path, exc_info=True)
            raise
        finally:
            elapsed = time.monotonic() - start
            await stats.request_finished(elapsed)
            logger.info("request done ip=%s status=%s duration=%.3fs", client_ip, status, elapsed)
