"""Общее состояние приложения: граф в памяти, симулятор, движок и публикация транзакций."""
import networkx as nx

from domain.enums import AppMode
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
    graph.clear()
    transactions.clear()
    simulator.reset_pool()
    if mode == AppMode.csv:
        simulator.accounts.clear()
        simulator.legit_pool.clear()
    engine = GraphEngine(graph, transactions, simulator.accounts)


def set_mode(new_mode: AppMode) -> None:
    """Переключает режим работы и сбрасывает данные (повторный вызов того же режима = очистка)."""
    global mode
    mode = new_mode
    simulator.paused = new_mode == AppMode.csv
    reset()


def add_to_graph(tx: Transaction) -> None:
    for acc_hash, bank in ((tx.from_hash, tx.from_bank), (tx.to_hash, tx.to_bank)):
        if acc_hash not in graph:
            acc = simulator.accounts.get(acc_hash)
            graph.add_node(
                acc_hash,
                bank_code=bank.value,
                account_type=acc.account_type.value if acc else "PERSONAL",
            )
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


async def publish(tx: Transaction) -> None:
    """Записывает транзакцию в граф и транслирует её всем WebSocket-клиентам."""
    add_to_graph(tx)
    engine.detect_suspects(tx)
    await manager.broadcast(tx.model_dump_json())
