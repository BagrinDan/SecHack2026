"""MuleTrace MD — FastAPI приложение: граф в памяти + живой WebSocket-поток транзакций MIA."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from enum import Enum
from typing import List, Optional

import networkx as nx
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph_engine import GraphEngine
from models import BankCode, DispersionGraph, MuleAlert, Transaction
from simulator import INJECTORS, Simulator

# Граф транзакций в памяти: узел = account_hash, ребро = транзакция (ключ ребра = tx_id).
graph: nx.MultiDiGraph = nx.MultiDiGraph()
transactions: dict = {}  # tx_id -> Transaction
simulator = Simulator()
engine = GraphEngine(graph, transactions, simulator.accounts)


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
    engine.detect_suspects(tx)
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


class Scenario(str, Enum):
    layered = "layered"
    business = "business"
    cycle = "cycle"


class TraceRequest(BaseModel):
    """Жалоба банка на мошенничество: транзакция, с которой начинается трассировка."""
    tx_id: str
    max_depth: int = 5


class SimulateResponse(BaseModel):
    scenario: Scenario
    root_tx_id: str
    tx_count: int
    alerts: List[MuleAlert]


def _trace(tx_id: str, max_depth: int) -> DispersionGraph:
    try:
        return engine.trace_funds(tx_id, max_depth)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown tx_id")


@app.post("/api/simulate/{scenario}", response_model=SimulateResponse)
async def simulate(scenario: Scenario):
    result = INJECTORS[scenario.value](simulator)
    for tx in result.transactions:
        await publish(tx)
    engine.trace_funds(result.root_tx_id)  # регистрирует дерево и поколения для алертов
    involved = {h for tx in result.transactions for h in (tx.from_hash, tx.to_hash)}
    alerts = [a for a in engine.list_alerts() if a.account_hash in involved]
    return SimulateResponse(
        scenario=scenario, root_tx_id=result.root_tx_id, tx_count=len(result.transactions), alerts=alerts
    )


@app.get("/api/trace/{tx_id}", response_model=DispersionGraph)
async def trace_get(tx_id: str, max_depth: int = Query(5, ge=1, le=5)):
    return _trace(tx_id, max_depth)


@app.post("/api/trace", response_model=DispersionGraph)
async def trace_post(req: TraceRequest):
    return _trace(req.tx_id, max(1, min(req.max_depth, 5)))


@app.get("/api/alerts", response_model=List[MuleAlert])
async def alerts(bank: Optional[BankCode] = None):
    return engine.list_alerts(bank)


@app.post("/api/accounts/{account_hash}/freeze")
async def freeze_account(account_hash: str):
    try:
        acc, prevented, already = engine.freeze(account_hash)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown account_hash")
    return {
        "account_hash": acc.account_hash,
        "bank_code": acc.bank_code,
        "status": acc.status,
        "prevented_mdl": prevented,
        "already_frozen": already,
    }


@app.get("/api/kpi")
async def kpi():
    return engine.kpi()


@app.websocket("/ws/transactions")
async def ws_transactions(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # держим соединение; клиентские сообщения игнорируются
    except WebSocketDisconnect:
        manager.disconnect(ws)
