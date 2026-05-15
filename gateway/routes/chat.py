import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from gateway.models.openai import ChatRequest, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _error(message: str, code: str, status: int = 500) -> JSONResponse:
    return JSONResponse(
        ErrorResponse(error=ErrorDetail(message=message, code=code)).model_dump(),
        status_code=status,
    )


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest, request: Request):
    adapter = request.app.state.adapter

    logger.info("chat model=%s stream=%s messages=%d", body.model, body.stream, len(body.messages))
    if body.stream:
        return await _stream_response(adapter, body)
    return await _json_response(adapter, body)


async def _json_response(adapter, body: ChatRequest) -> JSONResponse:
    try:
        response = await adapter.chat(body)
        logger.debug("chat complete finish_reason=%s tokens=%d",
                     response.choices[0].finish_reason if response.choices else None,
                     response.usage.total_tokens)
        return JSONResponse(response.model_dump())
    except Exception as exc:
        logger.error("chat error model=%s: %s", body.model, exc)
        return _error(str(exc), "backend_error")


async def _stream_response(adapter, body: ChatRequest) -> StreamingResponse:
    async def sse_generator():
        chunks = 0
        try:
            async for chunk in await adapter.stream_chat(body):
                chunks += 1
                yield f"data: {chunk.model_dump_json()}\n\n"
            logger.debug("stream complete model=%s chunks=%d", body.model, chunks)
        except Exception as exc:
            logger.error("stream error model=%s after %d chunks: %s", body.model, chunks, exc)
            err = ErrorResponse(error=ErrorDetail(message=str(exc), code="stream_error"))
            yield f"data: {err.model_dump_json()}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
