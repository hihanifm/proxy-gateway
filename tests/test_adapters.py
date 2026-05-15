import asyncio

import pytest

from gateway.adapters.stub import StubAdapter
from gateway.models.openai import ChatMessage, ChatRequest


@pytest.fixture()
def req():
    return ChatRequest(model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="Hi")])


def test_stub_chat(req):
    adapter = StubAdapter()
    resp = asyncio.run(adapter.chat(req))
    assert resp.object == "chat.completion"
    assert resp.choices[0].message.role == "assistant"
    assert isinstance(resp.choices[0].message.content, str)


def test_stub_stream(req):
    adapter = StubAdapter()

    async def collect():
        chunks = []
        async for chunk in await adapter.stream_chat(req):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(collect())
    assert len(chunks) > 0
    assert all(c.object == "chat.completion.chunk" for c in chunks)
    assert chunks[0].choices[0].delta.role == "assistant"
    assert chunks[-1].choices[0].finish_reason == "stop"
