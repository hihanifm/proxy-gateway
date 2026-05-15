from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

import httpx

from gateway.adapters.base import BaseAdapter
from gateway.models.openai import (
    ChatChunk,
    ChatRequest,
    ChatResponse,
    Delta,
    StreamChoice,
)


class OpenAIAdapter(BaseAdapter):
    """Transparent passthrough to the real OpenAI (or compatible) API."""

    def __init__(self, api_key: str, base_url: str, timeout: float) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        try:
            r = await self._client.post(
                "/chat/completions",
                json=request.model_dump(exclude_none=True),
            )
            r.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeError("OpenAI request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"OpenAI returned HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"OpenAI connection error: {exc}") from exc
        return ChatResponse.model_validate(r.json())

    async def stream_chat(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        return self._stream(request)

    async def _stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        body = request.model_dump(exclude_none=True)
        body["stream"] = True
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        try:
            async with self._client.stream("POST", "/chat/completions", json=body) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[len("data: "):]
                    if payload == "[DONE]":
                        break
                    data = json.loads(payload)
                    # Preserve the real chunk id from OpenAI
                    chunk_id = data.get("id", chunk_id)
                    yield ChatChunk.model_validate(data)
        except httpx.TimeoutException as exc:
            raise RuntimeError("OpenAI stream timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"OpenAI stream HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"OpenAI stream connection error: {exc}") from exc
