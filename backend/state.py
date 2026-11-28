"""Общее состояние приложения: граф в памяти, симулятор, движок и публикация транзакций."""
import networkx as nx

from domain.enums import AppMode, TxStatus
from domain.models import Transaction
from engine import GraphEngine
from network import ConnectionManager
from simulator import Simulator

# Граф транзакций в памяти: узел = account_hash, ребро = транзакция (ключ ребра = tx_id).
graph: nx.MultiDiGraph = nx.MultiDiGraph()
transactions: dict = {}  # tx_id -> Transaction
simulator = Simulator()
engine = GraphEngine(graph, transactions, simulator.accounts)
manager = ConnectionManager()
mode: AppMode = AppMode.simulator


def reset() -> None:
    """Полностью очищает данные. В режиме симулятора заново создаёт пул синтетических счетов."""
    global engine
    auto_prevent = engine.auto_prevent  # настройка автоблокировки переживает сброс данных
    graph.clear()
    transactions.clear()
    simulator.reset_pool()
    if mode == AppMode.csv:
        simulator.accounts.clear()
        simulator.legit_pool.clear()
    engine = GraphEngine(graph, transactions, simulator.accounts)
    engine.auto_prevent = auto_prevent


def set_mode(new_mode: AppMode) -> None:
    """Переключает режим работы и сбрасывает данные (повторный вызов того же режима = очистка)."""
    global mode
    mode = new_mode
    simulator.paused = new_mode == AppMode.csv
    reset()


def add_to_graph(tx: Transaction) -> list:
    """Добавляет транзакцию в граф; возвращает счета, которые появились в графе впервые."""
    created = []
    for acc_hash, bank in ((tx.from_hash, tx.from_bank), (tx.to_hash, tx.to_bank)):
        if acc_hash not in graph:
            acc = simulator.accounts.get(acc_hash)
            graph.add_node(
                acc_hash,
                bank_code=bank.value,
                account_type=acc.account_type.value if acc else "PERSONAL",
            )
            created.append(acc_hash)
    graph.add_edge(
        tx.from_hash,
        tx.to_hash,
        key=tx.tx_id,
        tx_id=tx.tx_id,
        timestamp=tx.timestamp,
        amount_mdl=tx.amount_mdl,
        channel=tx.channel.value,
    )
    transactions[tx.tx_id] = tx
    return created


def remove_from_graph(tx: Transaction, created: list) -> None:
    """Откатывает add_to_graph: убирает ребро и счета, которые этот перевод сам и добавил."""
    graph.remove_edge(tx.from_hash, tx.to_hash, key=tx.tx_id)
    transactions.pop(tx.tx_id, None)
    for acc_hash in created:
        if acc_hash in graph and graph.degree(acc_hash) == 0:
            graph.remove_node(acc_hash)


async def publish(tx: Transaction) -> bool:
    """Проводит транзакцию через граф и транслирует её всем WebSocket-клиентам.

    1. Если отправитель или получатель заморожен, перевод отклоняется сразу.
    2. Иначе он пробно добавляется в граф и проверяется правилами.
    3. Если он создаёт алерт, перевод откатывается из графа и получает статус BLOCKED,
       а счета замораживаются каскадом по цепочке.
    Отклонённый перевод виден в ленте (WebSocket), но в граф не попадает.
    Возвращает False, если перевод отклонён.
    """
    if not engine.screen(tx):
        await manager.broadcast(tx.model_dump_json())
        return False
    created = add_to_graph(tx)
    alerts = engine.detect_suspects(tx)
    if alerts and engine.auto_prevent:
        remove_from_graph(tx, created)
        engine.reject(tx)
        engine.forget_source(tx)
        engine.auto_freeze(alerts)
    await manager.broadcast(tx.model_dump_json())
    return tx.status != TxStatus.BLOCKED
