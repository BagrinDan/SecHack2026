"""Только чтение: удобные выборки по графу в памяти (узел = account_hash, ключ ребра = tx_id)."""
from __future__ import annotations

from typing import Dict, List, Optional

import networkx as nx

from domain.enums import BankCode
from domain.models import Account, Transaction


class GraphView:
    def __init__(
        self,
        graph: nx.MultiDiGraph,
        transactions: Dict[str, Transaction],
        accounts: Dict[str, Account],
    ) -> None:
        self.graph = graph
        self.transactions = transactions
        self.accounts = accounts

    def ins(self, node: str) -> List[Transaction]:
        """Входящие переводы узла по возрастанию времени."""
        txs = [self.transactions[k] for _, _, k in self.graph.in_edges(node, keys=True)]
        return sorted(txs, key=lambda t: t.timestamp)

    def outs(self, node: str) -> List[Transaction]:
        """Исходящие переводы узла по возрастанию времени."""
        txs = [self.transactions[k] for _, _, k in self.graph.out_edges(node, keys=True)]
        return sorted(txs, key=lambda t: t.timestamp)

    def bank_of(self, acc_hash: str) -> BankCode:
        acc = self.accounts.get(acc_hash)
        return acc.bank_code if acc else BankCode(self.graph.nodes[acc_hash]["bank_code"])


def avg_dwell(ins: List[Transaction], outs: List[Transaction]) -> Optional[float]:
    """Среднее время (сек) между последним входящим и каждым исходящим переводом."""
    vals = []
    for o in outs:
        prev = [i.timestamp for i in ins if i.timestamp < o.timestamp]
        if prev:
            vals.append((o.timestamp - max(prev)).total_seconds())
    return sum(vals) / len(vals) if vals else None
