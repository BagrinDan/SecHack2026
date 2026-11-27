from fastapi import APIRouter, HTTPException, Query

import state
from domain.models import DispersionGraph
from domain.request import TraceRequest

router = APIRouter(prefix="/api")


def _trace(tx_id: str, max_depth: int) -> DispersionGraph:
    try:
        return state.engine.trace_funds(tx_id, max_depth)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown tx_id")


@router.get("/trace/{tx_id}", response_model=DispersionGraph)
async def trace_get(tx_id: str, max_depth: int = Query(5, ge=1, le=5)):
    return _trace(tx_id, max_depth)


@router.post("/trace", response_model=DispersionGraph)
async def trace_post(req: TraceRequest):
    return _trace(req.tx_id, max(1, min(req.max_depth, 5)))
