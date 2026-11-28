from fastapi import APIRouter, HTTPException, Request

import state
from domain.enums import AppMode, TxStatus
from domain.responses import ImportResponse, ImportRowError
from ingest import CsvFormatError, parse_csv

router = APIRouter(prefix="/api")

MAX_BYTES = 10 * 1024 * 1024
MAX_ERRORS_REPORTED = 20


@router.post(
    "/import/csv",
    response_model=ImportResponse,
    openapi_extra={"requestBody": {"required": True, "content": {"text/csv": {"schema": {"type": "string"}}}}},
)
async def import_csv(request: Request):
    """Загружает CSV (тело запроса, UTF-8) и прогоняет транзакции по графу в порядке времени.

    Только в режиме csv. Предыдущие данные заменяются. Идентификаторы счетов токенизируются.
    Обязательные колонки: from, to, amount, timestamp, from_bank, to_bank.
    Необязательные: tx_id, channel, from_type, to_type.
    """
    if state.mode != AppMode.csv:
        raise HTTPException(status_code=409, detail="Загрузка CSV доступна в режиме csv: POST /api/mode/csv")
    body = await request.body()
    if len(body) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 10 МБ")
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Файл должен быть в кодировке UTF-8")
    try:
        parsed = parse_csv(text)
    except CsvFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not parsed.transactions:
        detail = "; ".join(f"строка {r}: {m}" for r, m in parsed.errors[:5]) or "в файле нет транзакций"
        raise HTTPException(status_code=422, detail=f"Нет ни одной корректной транзакции. {detail}")

    state.reset()
    for h, acc in parsed.accounts.items():
        state.simulator.accounts[h] = acc
    txs = sorted(parsed.transactions, key=lambda t: t.timestamp)  # правила опираются на порядок во времени
    for tx in txs:
        await state.publish(tx)

    rejected = [tx for tx in txs if tx.status == TxStatus.BLOCKED]
    involved = set(parsed.accounts)
    state.engine.trace_alerts(involved)
    alerts = [a for a in state.engine.list_alerts() if a.account_hash in involved]
    return ImportResponse(
        imported=len(txs),
        skipped=len(parsed.errors),
        accounts=len(parsed.accounts),
        blocked_tx_count=len(rejected),
        rejected_amount_mdl=round(sum(t.amount_mdl for t in rejected), 2),
        auto_frozen=sorted(state.engine.prevention.auto_frozen),
        period_from=txs[0].timestamp,
        period_to=txs[-1].timestamp,
        errors=[ImportRowError(row=r, error=m) for r, m in parsed.errors[:MAX_ERRORS_REPORTED]],
        root_tx_id=next((a.root_tx_id for a in alerts if a.root_tx_id), None),
        alerts=alerts,
    )
