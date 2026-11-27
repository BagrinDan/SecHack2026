"""RAPID_HOP: деньги ушли дальше быстрее чем за 10 минут."""
from domain.models import Transaction

from ..config import LARGE_MDL, RAPID_HOP_SEC
from ..view import GraphView


def rapid_hop(view: GraphView, tx: Transaction) -> bool:
    if tx.amount_mdl < LARGE_MDL:
        return False
    recent = sum(
        i.amount_mdl for i in view.ins(tx.from_hash)
        if 0 < (tx.timestamp - i.timestamp).total_seconds() <= RAPID_HOP_SEC
    )
    return recent >= 0.5 * tx.amount_mdl
