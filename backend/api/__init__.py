"""REST + WebSocket роутеры. Новый эндпоинт = новый модуль + строка здесь."""
from fastapi import APIRouter

from . import accounts, alerts, imports, kpi, mode, prevention, simulate, system, trace, ws

router = APIRouter()
for module in (system, mode, prevention, simulate, imports, trace, alerts, accounts, kpi, ws):
    router.include_router(module.router)
