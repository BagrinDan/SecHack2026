from fastapi import APIRouter, HTTPException

import state
from domain.enums import AppMode, Scenario
from domain.responses import SimulateResponse
from simulator import INJECTORS

router = APIRouter(prefix="/api")


@router.post("/simulate/{scenario}", response_model=SimulateResponse)
async def simulate(scenario: Scenario):
    if state.mode != AppMode.simulator:
        raise HTTPException(status_code=409, detail="Сценарии доступны в режиме simulator: POST /api/mode/simulator")
    result = INJECTORS[scenario.value](state.simulator)
    for tx in result.transactions:
        await state.publish(tx)
    state.engine.trace_funds(result.root_tx_id)  # регистрирует дерево и поколения для алертов
    involved = {h for tx in result.transactions for h in (tx.from_hash, tx.to_hash)}
    alerts = [a for a in state.engine.list_alerts() if a.account_hash in involved]
    return SimulateResponse(
        scenario=scenario, root_tx_id=result.root_tx_id, tx_count=len(result.transactions), alerts=alerts
    )
