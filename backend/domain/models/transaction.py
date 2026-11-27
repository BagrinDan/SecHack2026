import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from domain.enums import BankCode, Channel
from domain.helper import utcnow


class Transaction(BaseModel):
    tx_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: datetime = Field(default_factory=utcnow)
    from_hash: str
    to_hash: str
    from_bank: BankCode
    to_bank: BankCode
    amount_mdl: float = Field(gt=0)
    channel: Channel = Channel.MIA_P2P
