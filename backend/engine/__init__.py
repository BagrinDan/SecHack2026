"""Графовый движок MuleTrace MD: трассировка (Dispersion Tree) и скоринг счетов-мулов.

GraphEngine — фасад над модулями: view (выборки по графу), detection (правила), alerts (реестр),
tracing (дерево распределения), freezing (заморозка), kpi (аналитика).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

import networkx as nx

from domain.enums import BankCode
from domain.models import Account, DispersionGraph, MuleAlert, Transaction

from .alerts import AlertRegistry
from .detection import scan
from .freezing import FreezeLedger
from .kpi import Analytics
from .tracing import Tracer
from .view import GraphView


class GraphEngine:
    """Работает поверх графа в памяти: узел = account_hash, ключ ребра = tx_id."""

    def __init__(
        self,
        graph: nx.MultiDiGraph,
        transactions: Dict[str, Transaction],
        accounts: Dict[str, Account],
    ) -> None:
        self.view = GraphView(graph, transactions, accounts)
        self.registry = AlertRegistry(self.view)
        self.ledger = FreezeLedger(self.view)
        self.tracer = Tracer(self.view, self.registry)
        self.analytics = Analytics(self.view, self.registry, self.ledger)

    def trace_funds(self, start_tx_id: str, max_depth: int = 5) -> DispersionGraph:
        return self.tracer.trace_funds(start_tx_id, max_depth)

    def detect_suspects(self, tx: Transaction) -> List[MuleAlert]:
        """Проверяет паттерны после добавления `tx` в граф; возвращает новые/обновлённые алерты."""
        hits, senders = scan(self.view, tx)
        if senders is not None:
            self.registry.sources[tx.to_hash] = senders
        changed = []
        for h, rules in hits.items():
            alert = self.registry.apply(h, rules)
            if alert:
                changed.append(alert)
        return changed

    def trace_alerts(self, accounts: Set[str]) -> None:
        """Для алертов без дерева (данные из CSV) находит начало цепочки и регистрирует трассировку."""
        pending = sorted(
            (a for a in self.registry.alerts.values() if a.account_hash in accounts),
            key=lambda a: -a.risk_score,
        )
        for a in pending:
            if a.root_tx_id is not None:  # уже попал в дерево, построенное для другого алерта
                continue
            origin = self.tracer.origin_tx(a.account_hash)
            if origin is not None:
                self.tracer.trace_funds(origin.tx_id)

    def list_alerts(self, bank: Optional[BankCode] = None) -> List[MuleAlert]:
        return self.registry.list_alerts(bank)

    def freeze(self, acc_hash: str) -> Tuple[Account, float, bool]:
        return self.ledger.freeze(acc_hash)

    def kpi(self) -> dict:
        return self.analytics.kpi()
