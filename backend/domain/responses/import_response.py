from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from domain.models import MuleAlert


class ImportRowError(BaseModel):
    row: int  # номер строки в файле (заголовок = 1)
    error: str


class ImportResponse(BaseModel):
    imported: int
    skipped: int
    accounts: int
    blocked_tx_count: int = 0         # переводов отклонено автоблокировкой
    rejected_amount_mdl: float = 0.0  # сумма, которая не дошла до мулов
    auto_frozen: List[str] = Field(default_factory=list)  # счета, замороженные автоматически
    period_from: Optional[datetime] = None
    period_to: Optional[datetime] = None
    errors: List[ImportRowError]  # первые 20 ошибок
    root_tx_id: Optional[str] = None  # с чего начать трассировку: цепочка самого рискованного алерта
    alerts: List[MuleAlert]
