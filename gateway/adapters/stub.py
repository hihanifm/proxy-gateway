import asyncio
import uuid
from collections.abc import AsyncIterator

from gateway.adapters.base import BaseAdapter
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

_STUB_WORDS = ["Hello", " from", " the", " stub", " adapter", "!"]


class StubAdapter(BaseAdapter):
    async def chat(self, request: ChatRequest) -> ChatResponse:
        content = "".join(_STUB_WORDS)
        return ChatResponse(
            model=request.model,
            choices=[Choice(message=ChatMessage(role="assistant", content=content))],
            usage=UsageInfo(prompt_tokens=10, completion_tokens=6, total_tokens=16),
        )

    async def stream_chat(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        return self._stream(request)

    async def _stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        # role delta first
        yield ChatChunk(
            id=chunk_id,
            model=request.model,
            choices=[StreamChoice(delta=Delta(role="assistant"), finish_reason=None)],
        )

        for word in _STUB_WORDS:
            await asyncio.sleep(0.05)
            yield ChatChunk(
                id=chunk_id,
                model=request.model,
                choices=[StreamChoice(delta=Delta(content=word), finish_reason=None)],
            )

        # final chunk
        yield ChatChunk(
            id=chunk_id,
            model=request.model,
            choices=[StreamChoice(delta=Delta(), finish_reason="stop")],
        )
