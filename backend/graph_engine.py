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
    MuleAlert,
    Transaction,
    TxStatus,
)

WINDOW = timedelta(hours=24)   # окно, в котором исходящий перевод считается продолжением входящего
TEST_TX_MAX_MDL = 50.0         # перевод < 50 MDL считается тестовым

# Правила скоринга: название -> баллы.
RULE_POINTS = {
    "RAPID_HOP": 35,          # деньги ушли дальше быстрее чем за 10 мин
    "FAN_OUT": 30,            # крупное поступление раздроблено на 3+ перевода
    "CYCLING": 40,            # замкнутый цикл длиной 3–5 узлов
    "TEST_TRANSACTION": 25,   # микроперевод < 50 MDL перед переводом > 10 000 MDL
    "MULTI_TREE": 30,         # счёт участвует в нескольких деревьях распределения
}
ALERT_THRESHOLD = 60

PREVENT_MAX_DEPTH = 5         # глубина каскадной заморозки по дереву распределения
RAPID_HOP_SEC = 600
LARGE_MDL = 2_500.0           # выше максимума легитимного трафика симулятора (3 500) почти не бывает "в паре"
FANOUT_MIN_IN_MDL = 5_000.0
FANOUT_MIN_PARTS = 3
TEST_FOLLOWUP_MDL = 10_000.0
MULTI_SOURCE_MIN_MDL = 5_000.0
CYCLE_MIN_MDL = 1_000.0
CYCLE_MIN_EDGES, CYCLE_MAX_EDGES = 3, 5   # длина цикла в узлах = числу рёбер
CYCLE_AMOUNT_TOLERANCE = 0.85             # следующий перевод цикла не меньше 85% предыдущего


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
        self.alerts: Dict[str, MuleAlert] = {}
        self.trees: Dict[str, Set[str]] = defaultdict(set)    # счёт -> root_tx_id трассировок, где он был
        self.sources: Dict[str, Set[str]] = defaultdict(set)  # счёт -> отправители крупных поступлений
        self.generation: Dict[str, int] = {}                  # минимальное поколение из трассировок
        self.root_of: Dict[str, str] = {}                     # счёт -> первая трассировка с ним
        self.frozen_mdl: Dict[str, float] = {}                # замороженный счёт -> предотвращённая сумма
        self.auto_prevent = True                              # автозаморозка по алертам и отклонение переводов
        self.auto_frozen: Set[str] = set()                    # счета, замороженные автоматически
        self.rejected: List[Transaction] = []                 # отклонённые переводы (в граф не попадают)

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

        self._register_tree(root.tx_id, gen)
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

    # ---- скоринг ----
    def detect_suspects(self, tx: Transaction) -> List[MuleAlert]:
        """Проверяет паттерны после добавления `tx` в граф; возвращает новые/обновлённые алерты."""
        u, v = tx.from_hash, tx.to_hash
        hits: Dict[str, Set[str]] = defaultdict(set)
        if self._rapid_hop(tx):
            hits[u].add("RAPID_HOP")
        if self._fan_out(tx):
            hits[u].add("FAN_OUT")
        for h in self._cycle(tx):
            hits[h].add("CYCLING")
        for h in self._test_route(tx):
            hits[h].add("TEST_TRANSACTION")
        if self._multi_source(tx):
            hits[v].add("MULTI_TREE")
        changed = []
        for h, rules in hits.items():
            alert = self._apply(h, rules)
            if alert:
                changed.append(alert)
        return changed

    def _rapid_hop(self, tx: Transaction) -> bool:
        if tx.amount_mdl < LARGE_MDL:
            return False
        recent = sum(
            i.amount_mdl for i in self._in(tx.from_hash)
            if 0 < (tx.timestamp - i.timestamp).total_seconds() <= RAPID_HOP_SEC
        )
        return recent >= 0.5 * tx.amount_mdl

    def _fan_out(self, tx: Transaction) -> bool:
        outs = self._out(tx.from_hash)
        for i in self._in(tx.from_hash):
            if i.amount_mdl < FANOUT_MIN_IN_MDL or not (timedelta(0) < tx.timestamp - i.timestamp <= WINDOW):
                continue
            parts = [o for o in outs if i.timestamp < o.timestamp <= tx.timestamp]
            if len({o.to_hash for o in parts}) >= FANOUT_MIN_PARTS \
                    and sum(o.amount_mdl for o in parts) >= 0.5 * i.amount_mdl:
                return True
        return False

    def _cycle(self, tx: Transaction) -> Set[str]:
        """Ищет замкнутую цепочку v → … → u по возрастанию времени, которую закрывает `tx` (u → v)."""
        u, v = tx.from_hash, tx.to_hash
        budget = [2000]

        def dfs(cur: str, later: Transaction, k: int, nodes: Set[str]) -> Optional[Set[str]]:
            for e in self._in(cur):
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

    def _test_route(self, tx: Transaction) -> Set[str]:
        if tx.amount_mdl <= TEST_FOLLOWUP_MDL:
            return set()
        for t in self._out(tx.from_hash):
            if t.to_hash == tx.to_hash and t.amount_mdl < TEST_TX_MAX_MDL \
                    and timedelta(0) < tx.timestamp - t.timestamp <= WINDOW:
                return {tx.from_hash, tx.to_hash}
        return set()

    def _multi_source(self, tx: Transaction) -> bool:
        """Счёт получает крупные суммы от 2+ разных источников = лежит сразу в нескольких деревьях."""
        if tx.amount_mdl < MULTI_SOURCE_MIN_MDL:
            return False
        senders = {
            i.from_hash for i in self._in(tx.to_hash)
            if i.amount_mdl >= MULTI_SOURCE_MIN_MDL and timedelta(0) <= tx.timestamp - i.timestamp <= WINDOW
        }
        self.sources[tx.to_hash] = senders
        return len(senders) >= 2

    def _register_tree(self, root_tx_id: str, gen: Dict[str, int]) -> None:
        for h, g in gen.items():
            self.trees[h].add(root_tx_id)
            self.generation[h] = min(g, self.generation.get(h, g))
            self.root_of.setdefault(h, root_tx_id)
            if len(self.trees[h]) >= 2:
                self._apply(h, {"MULTI_TREE"})
            elif h in self.alerts:
                self._refresh_alert(h)

    def _apply(self, acc_hash: str, new_rules: Set[str]) -> Optional[MuleAlert]:
        """Добавляет сработавшие правила, пересчитывает риск; возвращает алерт, если он создан/изменён."""
        known = self.rules[acc_hash]
        if new_rules <= known:
            return None
        known |= new_rules
        score = min(100, sum(RULE_POINTS[r] for r in known))
        self.risk[acc_hash] = score
        acc = self.accounts.get(acc_hash)
        if acc:
            acc.risk_score = score
            if score >= ALERT_THRESHOLD and acc.status == AccountStatus.ACTIVE:
                acc.status = AccountStatus.SUSPECT
        if score < ALERT_THRESHOLD:
            return None
        return self._refresh_alert(acc_hash)

    def _refresh_alert(self, acc_hash: str) -> MuleAlert:
        alert = self.alerts.get(acc_hash)
        fields = dict(
            risk_score=self.risk[acc_hash],
            rules=sorted(self.rules[acc_hash]),
            generation=self.generation.get(acc_hash),
            root_tx_id=self.root_of.get(acc_hash),
            tree_count=max(1, len(self.trees[acc_hash]), len(self.sources.get(acc_hash, ()))),
        )
        if alert is None:
            acc = self.accounts.get(acc_hash)
            bank = acc.bank_code if acc else self._bank_of(acc_hash)
            alert = MuleAlert(account_hash=acc_hash, bank_code=bank, **fields)
            self.alerts[acc_hash] = alert
        else:
            for k, val in fields.items():
                setattr(alert, k, val)
        return alert

    def list_alerts(self, bank: Optional[BankCode] = None) -> List[MuleAlert]:
        for a in self.alerts.values():
            acc = self.accounts.get(a.account_hash)
            if acc:
                a.status = acc.status
        alerts = [a for a in self.alerts.values() if bank is None or a.bank_code == bank]
        return sorted(alerts, key=lambda a: (-a.risk_score, a.created_at))

    # ---- автопредотвращение ----
    def is_frozen(self, acc_hash: str) -> bool:
        acc = self.accounts.get(acc_hash)
        return acc is not None and acc.status == AccountStatus.FROZEN

    def screen(self, tx: Transaction) -> bool:
        """Проверка до проведения: True — перевод проходит, False — отклонён (статус BLOCKED)."""
        if self.auto_prevent and (self.is_frozen(tx.from_hash) or self.is_frozen(tx.to_hash)):
            self.reject(tx)
            return False
        return True

    def reject(self, tx: Transaction) -> None:
        tx.status = TxStatus.BLOCKED
        self.rejected.append(tx)

    def forget_source(self, tx: Transaction) -> None:
        """После отката отклонённого перевода убирает отправителя из источников получателя."""
        if not self.graph.has_edge(tx.from_hash, tx.to_hash):
            self.sources.get(tx.to_hash, set()).discard(tx.from_hash)

    def auto_freeze(self, alerts: List[MuleAlert]) -> List[str]:
        """Замораживает счета с алертами и каскадом всех получателей их исходящих переводов."""
        if not self.auto_prevent:
            return []
        frozen: List[str] = []
        queue = deque((a.account_hash, 0) for a in alerts)
        seen: Set[str] = set()
        while queue:
            node, depth = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            if node in self.accounts and not self.is_frozen(node):
                self.freeze(node)
                self.auto_frozen.add(node)
                frozen.append(node)
            if depth < PREVENT_MAX_DEPTH:
                for t in self._out(node):
                    queue.append((t.to_hash, depth + 1))
        return frozen

    # ---- заморозка и аналитика ----
    def freeze(self, acc_hash: str) -> Tuple[Account, float, bool]:
        """Симуляция блокировки. Возвращает (счёт, предотвращённая сумма MDL, был ли уже заморожен).

        Предотвращённая сумма: всё, что счёт пропустил дальше; для конечной точки — всё, что на него пришло.
        """
        acc = self.accounts[acc_hash]  # KeyError -> 404 в API
        already = acc.status == AccountStatus.FROZEN
        if not already:
            total_in = sum(t.amount_mdl for t in self._in(acc_hash))
            total_out = sum(t.amount_mdl for t in self._out(acc_hash))
            self.frozen_mdl[acc_hash] = round(total_out if total_out > 0 else total_in, 2)
            acc.status = AccountStatus.FROZEN
        return acc, self.frozen_mdl.get(acc_hash, 0.0), already

    def avg_dwell_sec(self, acc_hash: str) -> Optional[float]:
        ins, outs = self._in(acc_hash), self._out(acc_hash)
        vals = []
        for o in outs:
            prev = [i.timestamp for i in ins if i.timestamp < o.timestamp]
            if prev:
                vals.append((o.timestamp - max(prev)).total_seconds())
        return sum(vals) / len(vals) if vals else None

    def endpoint_hotlist(self, limit: int = 5) -> List[dict]:
        """Конечные точки вывода: счета из деревьев распределения, откуда деньги дальше не уходят."""
        rows = []
        for h in self.trees:
            if self.graph.out_degree(h) == 0:
                total_in = sum(t.amount_mdl for t in self._in(h))
                if total_in > 0:
                    acc = self.accounts.get(h)
                    bank = acc.bank_code if acc else self._bank_of(h)
                    rows.append({
                        "account_hash": h, "bank_code": bank.value, "total_in_mdl": round(total_in, 2),
                        "tree_count": len(self.trees[h]),
                        "status": acc.status.value if acc else "ACTIVE",
                    })
        return sorted(rows, key=lambda r: -r["total_in_mdl"])[:limit]

    def kpi(self) -> dict:
        dwells = [d for h in self.alerts if (d := self.avg_dwell_sec(h)) is not None]
        return {
            "transactions_checked": len(self.transactions),
            "mules_detected": len(self.alerts),
            "avg_dwell_time_sec": round(sum(dwells) / len(dwells), 1) if dwells else None,
            "blocked_amount_mdl": round(sum(self.frozen_mdl.values()), 2),
            "frozen_accounts": len(self.frozen_mdl),
            "auto_prevent": self.auto_prevent,
            "auto_frozen_accounts": len(self.auto_frozen),
            "blocked_tx_count": len(self.rejected),
            "rejected_amount_mdl": round(sum(t.amount_mdl for t in self.rejected), 2),
            "endpoint_hotlist": self.endpoint_hotlist(5),
        }
