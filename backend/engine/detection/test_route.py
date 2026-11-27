"""TEST_TRANSACTION: микроперевод < 50 MDL перед крупным переводом тому же получателю."""
from datetime import timedelta
from typing import Set

from domain.models import Transaction

from ..config import TEST_FOLLOWUP_MDL, TEST_TX_MAX_MDL, WINDOW
from ..view import GraphView


def test_route(view: GraphView, tx: Transaction) -> Set[str]:
    if tx.amount_mdl <= TEST_FOLLOWUP_MDL:
        return set()
    for t in view.outs(tx.from_hash):
        if t.to_hash == tx.to_hash and t.amount_mdl < TEST_TX_MAX_MDL \
                and timedelta(0) < tx.timestamp - t.timestamp <= WINDOW:
            return {tx.from_hash, tx.to_hash}
    return set()
