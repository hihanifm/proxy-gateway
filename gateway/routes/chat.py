from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from gateway.models.openai import ChatRequest, ErrorDetail, ErrorResponse

router = APIRouter()


def _error(message: str, code: str, status: int = 500) -> JSONResponse:
    return JSONResponse(
        ErrorResponse(error=ErrorDetail(message=message, code=code)).model_dump(),
        status_code=status,
    )


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest, request: Request):
    adapter = request.app.state.adapter

    if body.stream:
        return await _stream_response(adapter, body)
    return await _json_response(adapter, body)


async def _json_response(adapter, body: ChatRequest) -> JSONResponse:
    try:
        response = await adapter.chat(body)
        return JSONResponse(response.model_dump())
    except Exception as exc:
        return _error(str(exc), "backend_error")


async def _stream_response(adapter, body: ChatRequest) -> StreamingResponse:
    async def sse_generator():
        try:
            async for chunk in await adapter.stream_chat(body):
                yield f"data: {chunk.model_dump_json()}\n\n"
        except Exception as exc:
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
