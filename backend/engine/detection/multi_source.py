"""MULTI_TREE: счёт получает крупные суммы от 2+ разных источников = лежит сразу в нескольких деревьях."""
from datetime import timedelta
from typing import Optional, Set

from domain.models import Transaction

from ..config import MULTI_SOURCE_MIN_MDL, WINDOW
from ..view import GraphView


def multi_source_senders(view: GraphView, tx: Transaction) -> Optional[Set[str]]:
    """Отправители крупных поступлений на счёт получателя; None, если `tx` слишком мал для проверки."""
    if tx.amount_mdl < MULTI_SOURCE_MIN_MDL:
        return None
    return {
        i.from_hash for i in view.ins(tx.to_hash)
        if i.amount_mdl >= MULTI_SOURCE_MIN_MDL and timedelta(0) <= tx.timestamp - i.timestamp <= WINDOW
    }
