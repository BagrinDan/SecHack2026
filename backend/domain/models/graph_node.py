from typing import List, Optional

from pydantic import BaseModel, Field

from domain.enums import AccountStatus, AccountType, BankCode


class GraphNode(BaseModel):
    account_hash: str
    bank_code: BankCode
    account_type: AccountType
    status: AccountStatus
    generation: int = Field(ge=0, le=5)
    risk_score: int = Field(default=0, ge=0, le=100)
    rules: List[str] = Field(default_factory=list)
    total_in: float = 0.0
    total_out: float = 0.0
    fan_out: int = 0
    dwell_time_sec: Optional[float] = None  # среднее время удержания; None — деньги дальше не уходили
