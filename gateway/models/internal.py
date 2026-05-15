from pydantic import BaseModel


class InternalRequest(BaseModel):
    """Placeholder — fill in fields matching your proprietary backend schema."""
    prompt: str
    max_tokens: int | None = None
    temperature: float | None = None
    stream: bool = False


class InternalResponse(BaseModel):
    """Placeholder — fill in fields matching your proprietary backend response schema."""
    text: str
    finish_reason: str = "stop"
    prompt_tokens: int = 0
    completion_tokens: int = 0
