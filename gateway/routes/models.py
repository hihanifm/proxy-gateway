from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from gateway.config import settings
from gateway.models.openai import ModelCard, ModelList

router = APIRouter()


def _build_cards() -> list[ModelCard]:
    return [ModelCard(id=m) for m in settings.model_list()]


@router.get("/v1/models")
async def list_models():
    return ModelList(data=_build_cards())


@router.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    if model_id not in settings.model_list():
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return ModelCard(id=model_id)
