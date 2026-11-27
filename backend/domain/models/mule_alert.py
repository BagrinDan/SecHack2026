import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from domain.enums import AccountStatus, BankCode
from domain.helper import utcnow


class MuleAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    account_hash: str
    bank_code: BankCode
    risk_score: int = Field(ge=0, le=100)
    rules: List[str] = Field(default_factory=list)
    generation: Optional[int] = None
    root_tx_id: Optional[str] = None
    tree_count: int = 1  # в скольких деревьях распределения участвует счёт
    status: AccountStatus = AccountStatus.ACTIVE  # текущий статус счёта (FROZEN после блокировки)
    created_at: datetime = Field(default_factory=utcnow)
