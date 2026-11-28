from typing import List, Optional

from fastapi import APIRouter

import state
from domain.enums import BankCode
from domain.models import MuleAlert

router = APIRouter(prefix="/api")


@router.get("/alerts", response_model=List[MuleAlert])
async def alerts(bank: Optional[BankCode] = None):
    return state.engine.list_alerts(bank)
