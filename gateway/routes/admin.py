from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from gateway.config import settings

router = APIRouter()


class SwitchRequest(BaseModel):
    adapter: str
    backend_url: str | None = None
    api_key: str | None = None


@router.get("/v1/admin/config")
async def get_config(request: Request):
    return JSONResponse({
        "adapter": request.app.state.adapter_name,
        "backend_url": request.app.state.adapter_backend_url,
    })


@router.post("/v1/admin/switch")
async def switch_adapter(body: SwitchRequest, request: Request):
    from gateway.adapters.internal import InternalAdapter
    from gateway.adapters.openai_adapter import OpenAIAdapter
    from gateway.adapters.stub import StubAdapter

    name = body.adapter

    if name == "stub":
        new_adapter = StubAdapter()
        url = None

    elif name == "internal":
        # backend_url is advisory — InternalAdapter may ignore it and use its own routing.
        url = body.backend_url or settings.BACKEND_BASE_URL
        adapter = InternalAdapter()
        import httpx
        await adapter._client.aclose()
        adapter._client = httpx.AsyncClient(
            base_url=url,
            timeout=settings.BACKEND_TIMEOUT_S,
        )
        new_adapter = adapter

    elif name == "openai":
        key = body.api_key or settings.OPENAI_API_KEY
        if not key:
            return JSONResponse(
                {"error": "api_key required for openai adapter"},
                status_code=400,
            )
        url = body.backend_url or settings.OPENAI_BASE_URL
        new_adapter = OpenAIAdapter(api_key=key, base_url=url, timeout=settings.BACKEND_TIMEOUT_S)

    else:
        return JSONResponse(
            {"error": f"Unknown adapter '{name}'. Choose from: stub, internal, openai"},
            status_code=400,
        )

    request.app.state.adapter = new_adapter
    request.app.state.adapter_name = name
    request.app.state.adapter_backend_url = url

    return JSONResponse({"adapter": name, "backend_url": url})
