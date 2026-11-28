"""DEEP_CHAIN: перевод замыкает цепочку из 3+ крупных быстрых переводов подряд (3-е поколение мулов).

Жертва → G1 → G2 → G3: третий перевод (G2 → G3) уже доказывает расслоение, даже если ни G1, ни G2
не набрали порог по другим правилам (например, дробление было меньше чем на 3 счёта).
"""
from typing import Set

from domain.models import Transaction

from ..config import DEEP_CHAIN_HOP_SEC, DEEP_CHAIN_MAX_HOPS, DEEP_CHAIN_MIN_HOPS, LARGE_MDL
from ..view import GraphView


def chain_length(view: GraphView, tx: Transaction) -> int:
    """Число крупных переводов подряд, оканчивающихся на `tx` (каждый ушёл не позже HOP_SEC после прихода)."""
    budget = [500]

    def depth(cur: Transaction, visited: Set[str]) -> int:
        best = 1
        if best >= DEEP_CHAIN_MAX_HOPS:
            return best
        for i in view.ins(cur.from_hash):
            budget[0] -= 1
            if budget[0] < 0:
                break
            if i.amount_mdl < LARGE_MDL or i.from_hash in visited:
                continue
            if not 0 < (cur.timestamp - i.timestamp).total_seconds() <= DEEP_CHAIN_HOP_SEC:
                continue
            best = max(best, 1 + depth(i, visited | {i.from_hash}))
        return min(best, DEEP_CHAIN_MAX_HOPS)

    return depth(tx, {tx.from_hash, tx.to_hash})


def deep_chain(view: GraphView, tx: Transaction) -> Set[str]:
    """Счета-участники цепочки (отправитель и получатель), если `tx` — её звено №3 и дальше."""
    if tx.amount_mdl < LARGE_MDL:
        return set()
    return {tx.from_hash, tx.to_hash} if chain_length(view, tx) >= DEEP_CHAIN_MIN_HOPS else set()
