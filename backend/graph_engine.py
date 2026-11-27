"""Графовый движок MuleTrace MD: трассировка (Dispersion Tree) и скоринг счетов-мулов."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import timedelta
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx

from models import (
    Account,
    AccountStatus,
    AccountType,
    BankCode,
    DispersionGraph,
    GraphEdge,
    GraphNode,
    Transaction,
)

WINDOW = timedelta(hours=24)   # окно, в котором исходящий перевод считается продолжением входящего
TEST_TX_MAX_MDL = 50.0         # перевод < 50 MDL считается тестовым


class GraphEngine:
    """Работает поверх графа в памяти: узел = account_hash, ключ ребра = tx_id."""

    def __init__(
        self,
        graph: nx.MultiDiGraph,
        transactions: Dict[str, Transaction],
        accounts: Dict[str, Account],
    ) -> None:
        self.graph = graph
        self.transactions = transactions
        self.accounts = accounts
        self.risk: Dict[str, int] = {}
        self.rules: Dict[str, Set[str]] = defaultdict(set)

    # ---- выборки по узлу, отсортированные по времени ----
    def _in(self, node: str) -> List[Transaction]:
        txs = [self.transactions[k] for _, _, k in self.graph.in_edges(node, keys=True)]
        return sorted(txs, key=lambda t: t.timestamp)

    def _out(self, node: str) -> List[Transaction]:
        txs = [self.transactions[k] for _, _, k in self.graph.out_edges(node, keys=True)]
        return sorted(txs, key=lambda t: t.timestamp)

    # ---- трассировка ----
    def trace_funds(self, start_tx_id: str, max_depth: int = 5) -> DispersionGraph:
        """Обход графа вперёд по времени от мошеннической транзакции.

        Ребро следует за входящим, только если оно совершено ПОСЛЕ него и не позже чем через 24 ч.
        Поколение: 0 — жертва (отправитель стартовой транзакции), 1 — первый получатель и т.д.
        """
        root = self.transactions.get(start_tx_id)
        if root is None:
            raise KeyError(start_tx_id)
        max_depth = max(1, min(max_depth, 5))

        tree: Dict[str, Tuple[Transaction, int]] = {root.tx_id: (root, 1)}
        gen: Dict[str, int] = {root.from_hash: 0, root.to_hash: 1}
        queue = deque([(root, 1)])

        # Тот же маршрут после стартовой транзакции (тест 15 MDL → крупная сумма).
        for t in self._out(root.from_hash):
            if t.to_hash == root.to_hash and t.tx_id != root.tx_id \
                    and root.timestamp < t.timestamp <= root.timestamp + WINDOW:
                tree[t.tx_id] = (t, 1)
                queue.append((t, 1))

        while queue:
            e, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for t in self._out(e.to_hash):
                if t.tx_id in tree or not (e.timestamp < t.timestamp <= e.timestamp + WINDOW):
                    continue
                tree[t.tx_id] = (t, depth + 1)
                gen.setdefault(t.to_hash, depth + 1)  # BFS: первое появление = минимальное поколение
                queue.append((t, depth + 1))

        edges_txs = sorted((t for t, _ in tree.values()), key=lambda t: t.timestamp)
        nodes = [self._build_node(h, g, edges_txs) for h, g in gen.items()]
        nodes.sort(key=lambda n: (n.generation, n.account_hash))
        edges = [
            GraphEdge(
                tx_id=t.tx_id, **{"from": t.from_hash, "to": t.to_hash},
                amount_mdl=t.amount_mdl, timestamp=t.timestamp, channel=t.channel,
                is_test_tx=t.amount_mdl < TEST_TX_MAX_MDL, cross_bank=t.from_bank != t.to_bank,
            )
            for t in edges_txs
        ]
        return DispersionGraph(root_tx_id=root.tx_id, nodes=nodes, edges=edges)

    def _build_node(self, acc_hash: str, generation: int, tree_txs: List[Transaction]) -> GraphNode:
        ins = [t for t in tree_txs if t.to_hash == acc_hash]
        outs = [t for t in tree_txs if t.from_hash == acc_hash]
        dwells = []
        for o in outs:
            prev = [i.timestamp for i in ins if i.timestamp < o.timestamp]
            if prev:
                dwells.append((o.timestamp - max(prev)).total_seconds())
        acc = self.accounts.get(acc_hash)
        bank = acc.bank_code if acc else self._bank_of(acc_hash)
        return GraphNode(
            account_hash=acc_hash,
            bank_code=bank,
            account_type=acc.account_type if acc else AccountType.PERSONAL,
            status=acc.status if acc else AccountStatus.ACTIVE,
            generation=generation,
            risk_score=self.risk.get(acc_hash, 0),
            rules=sorted(self.rules.get(acc_hash, ())),
            total_in=round(sum(t.amount_mdl for t in ins), 2),
            total_out=round(sum(t.amount_mdl for t in outs), 2),
            fan_out=len(outs),
            dwell_time_sec=round(sum(dwells) / len(dwells), 1) if dwells else None,
        )

    def _bank_of(self, acc_hash: str) -> BankCode:
        return BankCode(self.graph.nodes[acc_hash]["bank_code"])
