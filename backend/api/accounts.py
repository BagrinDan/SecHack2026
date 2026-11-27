from fastapi import APIRouter, HTTPException

import state

router = APIRouter(prefix="/api")


@router.post("/accounts/{account_hash}/freeze")
async def freeze_account(account_hash: str):
    try:
        acc, prevented, already = state.engine.freeze(account_hash)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown account_hash")
    return {
        "account_hash": acc.account_hash,
        "bank_code": acc.bank_code,
        "status": acc.status,
        "prevented_mdl": prevented,
        "already_frozen": already,
    }
