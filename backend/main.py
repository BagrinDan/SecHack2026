"""MuleTrace MD — FastAPI приложение: граф в памяти + живой WebSocket-поток транзакций MIA."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import List

import networkx as nx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from models import Transaction
from simulator import Simulator

# Граф транзакций в памяти: узел = account_hash, ребро = транзакция (ключ ребра = tx_id).
graph: nx.MultiDiGraph = nx.MultiDiGraph()
transactions: dict = {}  # tx_id -> Transaction
simulator = Simulator()


class ConnectionManager:
    def __init__(self) -> None:
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: str) -> None:
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


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
    await manager.broadcast(tx.model_dump_json())


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop = asyncio.Event()
    task = asyncio.create_task(simulator.run_background(publish, stop))
    try:
        yield
    finally:
        stop.set()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="MuleTrace MD", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "service": "MuleTrace MD"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
    }


@app.websocket("/ws/transactions")
async def ws_transactions(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # держим соединение; клиентские сообщения игнорируются
    except WebSocketDisconnect:
        manager.disconnect(ws)
