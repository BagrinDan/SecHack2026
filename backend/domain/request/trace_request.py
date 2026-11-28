from pydantic import BaseModel


class TraceRequest(BaseModel):
    """Жалоба банка на мошенничество: транзакция, с которой начинается трассировка."""
    tx_id: str
    max_depth: int = 5
