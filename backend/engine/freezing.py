"""Заморозка счетов (симуляция блокировки через MIA Alert) и учёт предотвращённых сумм."""
from __future__ import annotations

from typing import Dict, Tuple

from domain.enums import AccountStatus
from domain.models import Account

from .view import GraphView


class FreezeLedger:
    def __init__(self, view: GraphView) -> None:
        self.view = view
        self.frozen_mdl: Dict[str, float] = {}  # замороженный счёт -> предотвращённая сумма

    def freeze(self, acc_hash: str) -> Tuple[Account, float, bool]:
        """Возвращает (счёт, предотвращённая сумма MDL, был ли уже заморожен).

        Предотвращённая сумма: всё, что счёт пропустил дальше; для конечной точки — всё, что на него пришло.
        """
        acc = self.view.accounts[acc_hash]  # KeyError -> 404 в API
        already = acc.status == AccountStatus.FROZEN
        if not already:
            total_in = sum(t.amount_mdl for t in self.view.ins(acc_hash))
            total_out = sum(t.amount_mdl for t in self.view.outs(acc_hash))
            self.frozen_mdl[acc_hash] = round(total_out if total_out > 0 else total_in, 2)
            acc.status = AccountStatus.FROZEN
        return acc, self.frozen_mdl.get(acc_hash, 0.0), already
