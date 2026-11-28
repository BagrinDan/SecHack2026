from fastapi import APIRouter, HTTPException

import state
from domain.enums import AppMode, Scenario, TxStatus
from domain.responses import SimulateResponse
from simulator import INJECTORS

router = APIRouter(prefix="/api")


@router.post("/simulate/{scenario}", response_model=SimulateResponse)
async def simulate(scenario: Scenario):
    if state.mode != AppMode.simulator:
        raise HTTPException(status_code=409, detail="Сценарии доступны в режиме simulator: POST /api/mode/simulator")
    result = INJECTORS[scenario.value](state.simulator)
    frozen_before = set(state.engine.prevention.auto_frozen)
    for tx in result.transactions:
        await state.publish(tx)
    if result.root_tx_id in state.transactions:
        state.engine.trace_funds(result.root_tx_id)  # регистрирует дерево и поколения для алертов
    rejected = [tx for tx in result.transactions if tx.status == TxStatus.BLOCKED]
    involved = {h for tx in result.transactions for h in (tx.from_hash, tx.to_hash)}
    alerts = [a for a in state.engine.list_alerts() if a.account_hash in involved]
    return SimulateResponse(
        scenario=scenario, root_tx_id=result.root_tx_id, tx_count=len(result.transactions),
        blocked_tx_count=len(rejected), rejected_amount_mdl=round(sum(t.amount_mdl for t in rejected), 2),
        auto_frozen=sorted(state.engine.prevention.auto_frozen - frozen_before), alerts=alerts,
    )
