from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from gateway.models.openai import ChatChunk, ChatRequest, ChatResponse


class BaseAdapter(ABC):
    # The backend_url passed via /v1/admin/switch is an advisory hint only.
    # Adapter implementations are free to ignore it and use their own routing
    # (e.g. an internal adapter may derive URLs from its own config or logic).
    # There is no contract that the hint will be honoured.

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse: ...

    @abstractmethod
    def stream_chat(self, request: ChatRequest) -> AsyncIterator[ChatChunk]: ...
