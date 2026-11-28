from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import Channel


class GraphEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tx_id: str
    from_hash: str = Field(alias="from")
    to_hash: str = Field(alias="to")
    amount_mdl: float
    timestamp: datetime
    channel: Channel = Channel.MIA_P2P
    is_test_tx: bool = False
    cross_bank: bool = False
