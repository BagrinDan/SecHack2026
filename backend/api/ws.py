from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import state

router = APIRouter()


@router.websocket("/ws/transactions")
async def ws_transactions(ws: WebSocket):
    await state.manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # держим соединение; клиентские сообщения игнорируются
    except WebSocketDisconnect:
        state.manager.disconnect(ws)
