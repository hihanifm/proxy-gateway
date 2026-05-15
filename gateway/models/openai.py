from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str | None = None
    name: str | None = None


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stop: str | list[str] | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    user: str | None = None


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class Choice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str | None = "stop"


class ChatResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[Choice]
    usage: UsageInfo = Field(default_factory=UsageInfo)


class Delta(BaseModel):
    role: str | None = None
    content: str | None = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: Delta
    finish_reason: str | None = None


class ChatChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[StreamChoice]


class ErrorDetail(BaseModel):
    message: str
    type: str = "gateway_error"
    code: str | None = None
    param: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ModelCard(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "organization"


class ModelList(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelCard]
