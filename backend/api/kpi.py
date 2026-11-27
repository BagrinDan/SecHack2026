from fastapi import APIRouter

import state

router = APIRouter(prefix="/api")


@router.get("/kpi")
async def kpi():
    return state.engine.kpi()
