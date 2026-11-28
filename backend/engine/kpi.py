"""Аналитика для дашборда: KPI и список конечных точек вывода."""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from domain.enums import BankCode

from .alerts import AlertRegistry
from .freezing import FreezeLedger
from .prevention import Prevention
from .view import GraphView, avg_dwell


class Analytics:
    def __init__(self, view: GraphView, registry: AlertRegistry, ledger: FreezeLedger, prevention: Prevention) -> None:
        self.view = view
        self.registry = registry
        self.ledger = ledger
        self.prevention = prevention

    def avg_dwell_sec(self, acc_hash: str) -> Optional[float]:
        return avg_dwell(self.view.ins(acc_hash), self.view.outs(acc_hash))

    def endpoint_hotlist(self, limit: int = 5) -> List[dict]:
        """Конечные точки вывода: счета из деревьев распределения, откуда деньги дальше не уходят."""
        rows = []
        for h in self.registry.trees:
            if self.view.graph.out_degree(h) == 0:
                total_in = sum(t.amount_mdl for t in self.view.ins(h))
                if total_in > 0:
                    acc = self.view.accounts.get(h)
                    rows.append({
                        "account_hash": h, "bank_code": self.view.bank_of(h).value,
                        "total_in_mdl": round(total_in, 2),
                        "tree_count": len(self.registry.trees[h]),
                        "status": acc.status.value if acc else "ACTIVE",
                    })
        return sorted(rows, key=lambda r: -r["total_in_mdl"])[:limit]

    def mules_by_bank(self) -> Dict[str, int]:
        counts = Counter(a.bank_code.value for a in self.registry.alerts.values())
        return {b.value: counts.get(b.value, 0) for b in BankCode}

    def kpi(self) -> dict:
        dwells = [d for h in self.registry.alerts if (d := self.avg_dwell_sec(h)) is not None]
        return {
            "transactions_checked": len(self.view.transactions),
            "mules_detected": len(self.registry.alerts),
            "avg_dwell_time_sec": round(sum(dwells) / len(dwells), 1) if dwells else None,
            "blocked_amount_mdl": round(sum(self.ledger.frozen_mdl.values()), 2),
            "frozen_accounts": len(self.ledger.frozen_mdl),
            "auto_prevent": self.prevention.enabled,
            "auto_frozen_accounts": len(self.prevention.auto_frozen),
            "blocked_tx_count": len(self.prevention.rejected),
            "rejected_amount_mdl": round(sum(t.amount_mdl for t in self.prevention.rejected), 2),
            "endpoint_hotlist": self.endpoint_hotlist(5),
            "mules_by_bank": self.mules_by_bank(),
        }
