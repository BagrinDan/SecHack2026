"""Реестр алертов: баллы риска по счетам, сработавшие правила, привязка к деревьям трассировки."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set

from domain.enums import AccountStatus, BankCode
from domain.models import MuleAlert

from .config import ALERT_THRESHOLD, RULE_POINTS
from .view import GraphView


class AlertRegistry:
    def __init__(self, view: GraphView) -> None:
        self.view = view
        self.risk: Dict[str, int] = {}
        self.rules: Dict[str, Set[str]] = defaultdict(set)
        self.alerts: Dict[str, MuleAlert] = {}
        self.trees: Dict[str, Set[str]] = defaultdict(set)    # счёт -> root_tx_id трассировок, где он был
        self.sources: Dict[str, Set[str]] = defaultdict(set)  # счёт -> отправители крупных поступлений
        self.generation: Dict[str, int] = {}                  # минимальное поколение из трассировок
        self.root_of: Dict[str, str] = {}                     # счёт -> первая трассировка с ним

    def apply(self, acc_hash: str, new_rules: Set[str]) -> Optional[MuleAlert]:
        """Добавляет сработавшие правила, пересчитывает риск; возвращает алерт, если он создан/изменён."""
        known = self.rules[acc_hash]
        if new_rules <= known:
            return None
        known |= new_rules
        score = min(100, sum(RULE_POINTS[r] for r in known))
        self.risk[acc_hash] = score
        acc = self.view.accounts.get(acc_hash)
        if acc:
            acc.risk_score = score
            if score >= ALERT_THRESHOLD and acc.status == AccountStatus.ACTIVE:
                acc.status = AccountStatus.SUSPECT
        if score < ALERT_THRESHOLD:
            return None
        return self.refresh(acc_hash)

    def refresh(self, acc_hash: str) -> MuleAlert:
        alert = self.alerts.get(acc_hash)
        fields = dict(
            risk_score=self.risk[acc_hash],
            rules=sorted(self.rules[acc_hash]),
            generation=self.generation.get(acc_hash),
            root_tx_id=self.root_of.get(acc_hash),
            tree_count=max(1, len(self.trees[acc_hash]), len(self.sources.get(acc_hash, ()))),
        )
        if alert is None:
            alert = MuleAlert(account_hash=acc_hash, bank_code=self.view.bank_of(acc_hash), **fields)
            self.alerts[acc_hash] = alert
        else:
            for k, val in fields.items():
                setattr(alert, k, val)
        return alert

    def register_tree(self, root_tx_id: str, gen: Dict[str, int]) -> None:
        """Запоминает, что счета из `gen` встретились в дереве `root_tx_id`; 2+ дерева = MULTI_TREE."""
        for h, g in gen.items():
            self.trees[h].add(root_tx_id)
            self.generation[h] = min(g, self.generation.get(h, g))
            self.root_of.setdefault(h, root_tx_id)
            if len(self.trees[h]) >= 2:
                self.apply(h, {"MULTI_TREE"})
            elif h in self.alerts:
                self.refresh(h)

    def list_alerts(self, bank: Optional[BankCode] = None) -> List[MuleAlert]:
        for a in self.alerts.values():
            acc = self.view.accounts.get(a.account_hash)
            if acc:
                a.status = acc.status
        alerts = [a for a in self.alerts.values() if bank is None or a.bank_code == bank]
        return sorted(alerts, key=lambda a: (-a.risk_score, a.created_at))
