from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from gateway.models.openai import ChatChunk, ChatRequest, ChatResponse


class BaseAdapter(ABC):
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse: ...

    @abstractmethod
    def stream_chat(self, request: ChatRequest) -> AsyncIterator[ChatChunk]: ...
