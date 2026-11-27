from fastapi import APIRouter

import state
from domain.enums import AppMode
from domain.responses import ModeResponse

router = APIRouter(prefix="/api")


@router.get("/mode", response_model=ModeResponse)
async def get_mode():
    return ModeResponse(mode=state.mode)


@router.post("/reset", response_model=ModeResponse)
async def reset_demo():
    """Чистый перезапуск перед показом: очищает граф, алерты и KPI, режим остаётся прежним."""
    state.reset()
    return ModeResponse(mode=state.mode)


@router.post("/mode/{mode}", response_model=ModeResponse)
async def switch_mode(mode: AppMode):
    """simulator — встроенный поток и сценарии атак; csv — данные из загруженного файла.

    Данные сбрасываются при каждом переключении (повторный вызов того же режима = очистка).
    """
    state.set_mode(mode)
    return ModeResponse(mode=state.mode)
