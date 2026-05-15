import asyncio
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI(title="Mock Internal LLM Backend")

MOCK_DELAY_MS = int(os.getenv("MOCK_DELAY_MS", "200"))
MOCK_WORDS = ["This", " is", " a", " mock", " backend", " response", "."]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/generate")
async def generate(request: Request):
    body = await request.json()
    stream = body.get("stream", False)
    await asyncio.sleep(MOCK_DELAY_MS / 1000)

    if stream:
        return StreamingResponse(
            _stream_words(),
            media_type="text/plain",
        )

    return JSONResponse({
        "text": "".join(MOCK_WORDS),
        "finish_reason": "stop",
        "prompt_tokens": 10,
        "completion_tokens": len(MOCK_WORDS),
    })


async def _stream_words():
    for word in MOCK_WORDS:
        await asyncio.sleep(0.05)
        yield word + "\n"
