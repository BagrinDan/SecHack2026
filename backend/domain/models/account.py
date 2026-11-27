from pydantic import BaseModel, Field

from domain.enums import AccountStatus, AccountType, BankCode
from domain.helper import HASH_LEN


class Account(BaseModel):
    account_hash: str = Field(min_length=HASH_LEN, max_length=HASH_LEN)
    bank_code: BankCode
    account_type: AccountType = AccountType.PERSONAL
    status: AccountStatus = AccountStatus.ACTIVE
    risk_score: int = Field(default=0, ge=0, le=100)
