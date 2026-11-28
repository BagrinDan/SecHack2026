"""Автопредотвращение: отклонение переводов с замороженных счетов и каскадная заморозка по алертам."""
from __future__ import annotations

from collections import deque
from typing import List, Set

from domain.enums import AccountStatus, TxStatus
from domain.models import MuleAlert, Transaction

from .alerts import AlertRegistry
from .config import PREVENT_MAX_DEPTH, PREVENT_MAX_FROZEN, PREVENT_MIN_MDL, WINDOW
from .freezing import FreezeLedger
from .view import GraphView


class Prevention:
    def __init__(self, view: GraphView, registry: AlertRegistry, ledger: FreezeLedger) -> None:
        self.view = view
        self.registry = registry
        self.ledger = ledger
        self.enabled = True                       # автозаморозка по алертам и отклонение переводов
        self.auto_frozen: Set[str] = set()        # счета, замороженные автоматически
        self.rejected: List[Transaction] = []     # отклонённые переводы (в граф не попадают)

    def is_frozen(self, acc_hash: str) -> bool:
        acc = self.view.accounts.get(acc_hash)
        return acc is not None and acc.status == AccountStatus.FROZEN

    def screen(self, tx: Transaction) -> bool:
        """Проверка до проведения: True — перевод проходит, False — отклонён (статус BLOCKED)."""
        if self.enabled and (self.is_frozen(tx.from_hash) or self.is_frozen(tx.to_hash)):
            self.reject(tx)
            return False
        return True

    def reject(self, tx: Transaction) -> None:
        tx.status = TxStatus.BLOCKED
        self.rejected.append(tx)

    def forget_source(self, tx: Transaction) -> None:
        """После отката отклонённого перевода убирает отправителя из источников получателя."""
        if not self.view.graph.has_edge(tx.from_hash, tx.to_hash):
            self.registry.sources.get(tx.to_hash, set()).discard(tx.from_hash)

    def auto_freeze(self, alerts: List[MuleAlert]) -> List[str]:
        """Замораживает счета с алертами и счета, куда ушли их деньги.

        Каскад идёт только вперёд во времени: перевод считается продолжением входящего, если он
        позже него, в пределах окна WINDOW. Мелкие переводы (< PREVENT_MIN_MDL) его не продолжают,
        а число замороженных за один каскад ограничено PREVENT_MAX_FROZEN.
        """
        if not self.enabled:
            return []
        frozen: List[str] = []
        queue = deque((a.account_hash, 0, None) for a in alerts)  # (счёт, глубина, пришедший перевод)
        seen: Set[str] = set()
        while queue and len(frozen) < PREVENT_MAX_FROZEN:
            node, depth, inc = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            if node in self.view.accounts and not self.is_frozen(node):
                self.ledger.freeze(node)
                self.auto_frozen.add(node)
                frozen.append(node)
            if depth >= PREVENT_MAX_DEPTH:
                continue
            for t in self.view.outs(node):
                if t.amount_mdl < PREVENT_MIN_MDL:
                    continue
                if inc is not None and not (inc.timestamp < t.timestamp <= inc.timestamp + WINDOW):
                    continue
                queue.append((t.to_hash, depth + 1, t))
        return frozen
