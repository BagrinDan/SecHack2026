from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from domain.models import MuleAlert


class ImportRowError(BaseModel):
    row: int  # номер строки в файле (заголовок = 1)
    error: str


class ImportResponse(BaseModel):
    imported: int
    skipped: int
    accounts: int
    period_from: Optional[datetime] = None
    period_to: Optional[datetime] = None
    errors: List[ImportRowError]  # первые 20 ошибок
    root_tx_id: Optional[str] = None  # с чего начать трассировку: цепочка самого рискованного алерта
    alerts: List[MuleAlert]
