"""Zero-PII схемы данных MuleTrace MD.

Счета хранятся только как токены (первые 12 символов SHA-256 с солью от IBAN/телефона).
ФИО, IDNP и реальные IBAN в системе не хранятся.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# Соль фиксирована для прототипа (в проде — секрет в KMS, общий для банков-участников MIA).
HASH_SALT = "muletrace-md-2026"
HASH_LEN = 12


class BankCode(str, Enum):
    MAIB = "MAIB"
    MICB = "MICB"
    VICTORIABANK = "VICTORIABANK"
    OTP = "OTP"
    FINCOMBANK = "FINCOMBANK"


class AccountType(str, Enum):
    PERSONAL = "PERSONAL"
    BUSINESS = "BUSINESS"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPECT = "SUSPECT"
    FROZEN = "FROZEN"


class Channel(str, Enum):
    MIA_P2P = "MIA_P2P"
    MIA_QR = "MIA_QR"


def tokenize(identifier: str) -> str:
    """Zero-PII токен: первые 12 символов SHA-256(salt + IBAN/телефон)."""
    return hashlib.sha256((HASH_SALT + identifier).encode("utf-8")).hexdigest()[:HASH_LEN]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Account(BaseModel):
    account_hash: str = Field(min_length=HASH_LEN, max_length=HASH_LEN)
    bank_code: BankCode
    account_type: AccountType = AccountType.PERSONAL
    status: AccountStatus = AccountStatus.ACTIVE
    risk_score: int = Field(default=0, ge=0, le=100)


class Transaction(BaseModel):
    tx_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: datetime = Field(default_factory=utcnow)
    from_hash: str
    to_hash: str
    from_bank: BankCode
    to_bank: BankCode
    amount_mdl: float = Field(gt=0)
    channel: Channel = Channel.MIA_P2P


class MuleAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    account_hash: str
    bank_code: BankCode
    risk_score: int = Field(ge=0, le=100)
    rules: List[str] = Field(default_factory=list)
    generation: Optional[int] = None
    root_tx_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class GraphNode(BaseModel):
    account_hash: str
    bank_code: BankCode
    account_type: AccountType
    status: AccountStatus
    generation: int
    risk_score: int = 0
    total_in: float = 0.0
    total_out: float = 0.0
    dwell_time_sec: Optional[float] = None


class GraphEdge(BaseModel):
    tx_id: str
    source: str
    target: str
    amount_mdl: float
    timestamp: datetime
    is_test: bool = False


class DispersionGraph(BaseModel):
    root_tx_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
