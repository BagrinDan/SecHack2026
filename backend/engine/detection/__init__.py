"""Правила обнаружения мулов: по одному файлу на правило. Новое правило = новый файл + строка в scan()."""
from collections import defaultdict
from typing import Dict, Optional, Set, Tuple

from domain.models import Transaction

from ..view import GraphView
from .cycle import cycle
from .fan_out import fan_out
from .multi_source import multi_source_senders
from .rapid_hop import rapid_hop
from .test_route import test_route


def scan(view: GraphView, tx: Transaction) -> Tuple[Dict[str, Set[str]], Optional[Set[str]]]:
    """Проверяет паттерны после добавления `tx` в граф.

    Возвращает (счёт -> сработавшие правила, отправители крупных поступлений получателю или None).
    """
    u, v = tx.from_hash, tx.to_hash
    hits: Dict[str, Set[str]] = defaultdict(set)
    if rapid_hop(view, tx):
        hits[u].add("RAPID_HOP")
    if fan_out(view, tx):
        hits[u].add("FAN_OUT")
    for h in cycle(view, tx):
        hits[h].add("CYCLING")
    for h in test_route(view, tx):
        hits[h].add("TEST_TRANSACTION")
    senders = multi_source_senders(view, tx)
    if senders is not None and len(senders) >= 2:
        hits[v].add("MULTI_TREE")
    return hits, senders
