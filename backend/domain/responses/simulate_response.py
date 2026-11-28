from typing import List

from pydantic import BaseModel, Field

from domain.enums import Scenario
from domain.models import MuleAlert


class SimulateResponse(BaseModel):
    scenario: Scenario
    root_tx_id: str
    tx_count: int
    blocked_tx_count: int = 0         # переводов отклонено автоблокировкой
    rejected_amount_mdl: float = 0.0  # сумма, которая не дошла до мулов
    auto_frozen: List[str] = Field(default_factory=list)  # счета, замороженные автоматически в этом прогоне
    alerts: List[MuleAlert]
