from typing import List

from pydantic import BaseModel

from domain.enums import Scenario
from domain.models import MuleAlert


class SimulateResponse(BaseModel):
    scenario: Scenario
    root_tx_id: str
    tx_count: int
    alerts: List[MuleAlert]
