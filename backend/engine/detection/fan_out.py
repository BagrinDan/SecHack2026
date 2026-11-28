"""FAN_OUT: крупное поступление раздроблено на 3+ перевода разным получателям."""
from datetime import timedelta

from domain.models import Transaction

from ..config import FANOUT_MIN_IN_MDL, FANOUT_MIN_PARTS, WINDOW
from ..view import GraphView


def fan_out(view: GraphView, tx: Transaction) -> bool:
    outs = view.outs(tx.from_hash)
    for i in view.ins(tx.from_hash):
        if i.amount_mdl < FANOUT_MIN_IN_MDL or not (timedelta(0) < tx.timestamp - i.timestamp <= WINDOW):
            continue
        parts = [o for o in outs if i.timestamp < o.timestamp <= tx.timestamp]
        if len({o.to_hash for o in parts}) >= FANOUT_MIN_PARTS \
                and sum(o.amount_mdl for o in parts) >= 0.5 * i.amount_mdl:
            return True
    return False
