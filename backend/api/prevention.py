from fastapi import APIRouter

import state
from domain.request import AutoPreventRequest
from domain.responses import PreventionResponse

router = APIRouter(prefix="/api")


@router.get("/auto-prevent", response_model=PreventionResponse)
async def get_auto_prevent():
    return PreventionResponse(enabled=state.engine.auto_prevent)


@router.post("/auto-prevent", response_model=PreventionResponse)
async def set_auto_prevent(req: AutoPreventRequest):
    """Автоблокировка: отклонение переводов с замороженных счетов и каскадная заморозка по алертам.

    Если выключена, система только создаёт алерты, а заморозка остаётся ручной.
    """
    state.engine.auto_prevent = req.enabled
    return PreventionResponse(enabled=state.engine.auto_prevent)
