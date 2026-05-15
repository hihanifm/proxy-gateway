from gateway.adapters.base import BaseAdapter
from gateway.config import settings


def get_adapter() -> BaseAdapter:
    from gateway.adapters.internal import InternalAdapter
    from gateway.adapters.openai_adapter import OpenAIAdapter
    from gateway.adapters.stub import StubAdapter

    name = settings.GATEWAY_ADAPTER

    if name == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set when GATEWAY_ADAPTER=openai")
        return OpenAIAdapter(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            timeout=settings.BACKEND_TIMEOUT_S,
        )

    registry: dict[str, type[BaseAdapter]] = {
        "stub": StubAdapter,
        "internal": InternalAdapter,
    }
    cls = registry.get(name)
    if cls is None:
        raise ValueError(f"Unknown adapter '{name}'. Choose from: openai, {list(registry)}")
    return cls()
