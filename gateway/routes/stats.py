from fastapi import APIRouter
from fastapi.responses import JSONResponse

from gateway.stats import stats

router = APIRouter()


@router.get("/v1/stats")
async def get_stats():
    return JSONResponse(stats.snapshot())
