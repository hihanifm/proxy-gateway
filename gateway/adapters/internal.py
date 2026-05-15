from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator

import httpx

logger = logging.getLogger(__name__)

from gateway.adapters.base import BaseAdapter
from gateway.config import settings
from gateway.models.internal import InternalRequest, InternalResponse
from gateway.models.openai import (
    ChatChunk,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Choice,
    Delta,
    StreamChoice,
    UsageInfo,
)


class InternalAdapter(BaseAdapter):
    """Translates OpenAI ChatRequest <-> proprietary internal HTTP/REST backend.

    Fill in _to_internal() and _from_internal() once the backend schema is finalized.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url or settings.BACKEND_BASE_URL,
            timeout=settings.BACKEND_TIMEOUT_S,
        )

    def _to_internal(self, request: ChatRequest) -> InternalRequest:
        # Flatten messages into a single prompt — replace with your actual mapping.
        prompt = "\n".join(
            f"{m.role}: {m.content}" for m in request.messages if m.content
        )
        return InternalRequest(
            prompt=prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=request.stream,
        )

    def _from_internal(self, model: str, resp: InternalResponse) -> ChatResponse:
        return ChatResponse(
            model=model,
            choices=[
                Choice(
                    message=ChatMessage(role="assistant", content=resp.text),
                    finish_reason=resp.finish_reason,
                )
            ],
            usage=UsageInfo(
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                total_tokens=resp.prompt_tokens + resp.completion_tokens,
            ),
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        payload = self._to_internal(request)
        url = str(self._client.base_url) + "v1/generate"
        logger.debug("backend POST %s", url)
        start = time.monotonic()
        try:
            r = await self._client.post("/v1/generate", json=payload.model_dump())
            r.raise_for_status()
            logger.debug("backend response status=%d duration=%.3fs", r.status_code, time.monotonic() - start)
        except httpx.TimeoutException as exc:
            logger.warning("backend timeout url=%s duration=%.3fs", url, time.monotonic() - start)
            raise RuntimeError("Backend request timed out") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("backend http_error status=%d url=%s", exc.response.status_code, url)
            raise RuntimeError(f"Backend returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.warning("backend connection_error url=%s error=%s", url, exc)
            raise RuntimeError(f"Backend connection error: {exc}") from exc

        internal_resp = InternalResponse.model_validate(r.json())
        return self._from_internal(request.model, internal_resp)

    async def stream_chat(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        return self._stream(request)

    async def _stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        payload = self._to_internal(request)
        payload.stream = True
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        yield ChatChunk(
            id=chunk_id,
            model=request.model,
            choices=[StreamChoice(delta=Delta(role="assistant"), finish_reason=None)],
        )

        try:
            async with self._client.stream(
                "POST", "/v1/generate", json=payload.model_dump()
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    # Backend is expected to send plain text lines when streaming.
                    # Adjust parsing here once the real streaming protocol is known.
                    yield ChatChunk(
                        id=chunk_id,
                        model=request.model,
                        choices=[StreamChoice(delta=Delta(content=line), finish_reason=None)],
                    )
        except httpx.TimeoutException as exc:
            raise RuntimeError("Backend stream timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Backend stream HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Backend stream connection error: {exc}") from exc

        yield ChatChunk(
            id=chunk_id,
            model=request.model,
            choices=[StreamChoice(delta=Delta(), finish_reason="stop")],
        )
