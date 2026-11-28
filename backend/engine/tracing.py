"""Трассировка Dispersion Tree: обход графа вперёд по времени от мошеннической транзакции."""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Tuple

from domain.enums import AccountStatus, AccountType
from domain.models import DispersionGraph, GraphEdge, GraphNode, Transaction

from .alerts import AlertRegistry
from .config import TEST_TX_MAX_MDL, WINDOW
from .view import GraphView, avg_dwell


class Tracer:
    def __init__(self, view: GraphView, registry: AlertRegistry) -> None:
        self.view = view
        self.registry = registry

    def trace_funds(self, start_tx_id: str, max_depth: int = 5) -> DispersionGraph:
        """Ребро следует за входящим, только если оно совершено ПОСЛЕ него и не позже чем через 24 ч.

        Поколение: 0 — жертва (отправитель стартовой транзакции), 1 — первый получатель и т.д.
        """
        root = self.view.transactions.get(start_tx_id)
        if root is None:
            raise KeyError(start_tx_id)
        max_depth = max(1, min(max_depth, 5))

        tree: Dict[str, Tuple[Transaction, int]] = {root.tx_id: (root, 1)}
        gen: Dict[str, int] = {root.from_hash: 0, root.to_hash: 1}
        queue = deque([(root, 1)])

        # Тот же маршрут после стартовой транзакции (тест 15 MDL → крупная сумма).
        for t in self.view.outs(root.from_hash):
            if t.to_hash == root.to_hash and t.tx_id != root.tx_id \
                    and root.timestamp < t.timestamp <= root.timestamp + WINDOW:
                tree[t.tx_id] = (t, 1)
                queue.append((t, 1))

        while queue:
            e, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for t in self.view.outs(e.to_hash):
                if t.tx_id in tree or not (e.timestamp < t.timestamp <= e.timestamp + WINDOW):
                    continue
                tree[t.tx_id] = (t, depth + 1)
                gen.setdefault(t.to_hash, depth + 1)  # BFS: первое появление = минимальное поколение
                queue.append((t, depth + 1))

        self.registry.register_tree(root.tx_id, gen)
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

    def origin_tx(self, acc_hash: str, max_back: int = 5) -> Optional[Transaction]:
        """Транзакция, с которой начинается цепочка, приведшая деньги на счёт.

        Идём назад по самому крупному входящему переводу (в пределах окна 24 ч до следующего звена).
        """
        found: Optional[Transaction] = None
        cur = acc_hash
        for _ in range(max_back):
            ins = self.view.ins(cur)
            if found is not None:
                ins = [t for t in ins if t.timestamp < found.timestamp and found.timestamp - t.timestamp <= WINDOW]
            if not ins:
                break
            found = max(ins, key=lambda t: t.amount_mdl)
            cur = found.from_hash
        return found

    def _build_node(self, acc_hash: str, generation: int, tree_txs: List[Transaction]) -> GraphNode:
        ins = [t for t in tree_txs if t.to_hash == acc_hash]
        outs = [t for t in tree_txs if t.from_hash == acc_hash]
        dwell = avg_dwell(ins, outs)
        acc = self.view.accounts.get(acc_hash)
        return GraphNode(
            account_hash=acc_hash,
            bank_code=self.view.bank_of(acc_hash),
            account_type=acc.account_type if acc else AccountType.PERSONAL,
            status=acc.status if acc else AccountStatus.ACTIVE,
            generation=generation,
            risk_score=self.registry.risk.get(acc_hash, 0),
            rules=sorted(self.registry.rules.get(acc_hash, ())),
            total_in=round(sum(t.amount_mdl for t in ins), 2),
            total_out=round(sum(t.amount_mdl for t in outs), 2),
            fan_out=len(outs),
            dwell_time_sec=round(dwell, 1) if dwell is not None else None,
        )
