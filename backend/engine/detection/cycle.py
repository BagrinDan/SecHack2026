"""CYCLING: замкнутая цепочка 3–5 узлов с почти одинаковой суммой."""
from typing import Optional, Set

from domain.models import Transaction

from ..config import CYCLE_AMOUNT_TOLERANCE, CYCLE_MAX_EDGES, CYCLE_MIN_EDGES, CYCLE_MIN_MDL, WINDOW
from ..view import GraphView


def cycle(view: GraphView, tx: Transaction) -> Set[str]:
    """Ищет замкнутую цепочку v → … → u по возрастанию времени, которую закрывает `tx` (u → v)."""
    u, v = tx.from_hash, tx.to_hash
    budget = [2000]

    def dfs(cur: str, later: Transaction, k: int, nodes: Set[str]) -> Optional[Set[str]]:
        for e in view.ins(cur):
            budget[0] -= 1
            if budget[0] < 0:
                return None
            if not (e.timestamp < later.timestamp and tx.timestamp - e.timestamp <= WINDOW):
                continue
            if e.amount_mdl < CYCLE_MIN_MDL or later.amount_mdl < CYCLE_AMOUNT_TOLERANCE * e.amount_mdl \
                    or later.amount_mdl > 1.02 * e.amount_mdl:
                continue
            if e.from_hash == v:
                if k + 1 >= CYCLE_MIN_EDGES:
                    return nodes | {v}
            elif e.from_hash not in nodes and k + 1 < CYCLE_MAX_EDGES:
                found = dfs(e.from_hash, e, k + 1, nodes | {e.from_hash})
                if found:
                    return found
        return None

    if tx.amount_mdl < CYCLE_MIN_MDL or u == v:
        return set()
    return dfs(u, tx, 1, {u}) or set()
