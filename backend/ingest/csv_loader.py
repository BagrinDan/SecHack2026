"""Загрузка транзакций из CSV: валидация строк и токенизация идентификаторов счетов (Zero-PII).

Сырые IBAN, номера телефонов и любые другие идентификаторы после разбора файла нигде не хранятся:
счёт превращается в токен функцией tokenize. Уже готовый токен (12 hex-символов) принимается как есть.
"""
from __future__ import annotations

import csv
import io
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from domain.enums import AccountType, BankCode, Channel
from domain.helper import HASH_LEN, tokenize
from domain.models import Account, Transaction

MAX_ROWS = 20_000

# Каноничное имя колонки -> допустимые заголовки (регистр и пробелы не важны).
ALIASES: Dict[str, Tuple[str, ...]] = {
    "from": ("from", "from_account", "from_hash", "sender", "src", "source"),
    "to": ("to", "to_account", "to_hash", "receiver", "dst", "destination"),
    "amount": ("amount_mdl", "amount", "sum"),
    "timestamp": ("timestamp", "time", "datetime", "date", "ts"),
    "from_bank": ("from_bank", "sender_bank", "src_bank", "source_bank"),
    "to_bank": ("to_bank", "receiver_bank", "dst_bank", "destination_bank"),
    "tx_id": ("tx_id", "id", "transaction_id"),
    "channel": ("channel",),
    "from_type": ("from_type", "sender_type"),
    "to_type": ("to_type", "receiver_type"),
}
REQUIRED = ("from", "to", "amount", "timestamp", "from_bank", "to_bank")
BANK_ALIASES = {"OTPBANK": "OTP", "FINCOM": "FINCOMBANK"}
_TOKEN = re.compile(rf"^[0-9a-f]{{{HASH_LEN}}}$")


class CsvFormatError(ValueError):
    """Проблема всего файла: нет нужных колонок, слишком много строк, пустой файл."""


@dataclass
class ParsedCsv:
    transactions: List[Transaction] = field(default_factory=list)
    accounts: Dict[str, Account] = field(default_factory=dict)
    errors: List[Tuple[int, str]] = field(default_factory=list)  # (номер строки в файле, причина)


def to_token(raw: str) -> str:
    raw = raw.strip()
    return raw.lower() if _TOKEN.match(raw.lower()) else tokenize(raw)


def _parse_amount(s: str) -> float:
    s = s.replace(" ", "").replace(" ", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        raise ValueError(f"сумма '{s}' не число") from None
    if not math.isfinite(v) or v <= 0:
        raise ValueError(f"сумма должна быть больше нуля, получено '{s}'")
    return round(v, 2)


def _parse_time(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        raise ValueError(f"не удалось разобрать время '{s}' (ожидается ISO 8601, например 2026-11-27T10:00:00)") from None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _parse_bank(s: str) -> BankCode:
    name = re.sub(r"[^A-Z]", "", s.upper())
    try:
        return BankCode(BANK_ALIASES.get(name, name))
    except ValueError:
        raise ValueError(f"неизвестный банк '{s}', допустимо: {', '.join(b.value for b in BankCode)}") from None


def _parse_enum(enum_cls, s: str, default, label: str):
    if not s:
        return default
    try:
        return enum_cls(s.strip().upper())
    except ValueError:
        raise ValueError(f"неизвестное значение {label} '{s}', допустимо: {', '.join(e.value for e in enum_cls)}") from None


def _detect_delimiter(header_line: str) -> str:
    return max(",;\t|", key=header_line.count)


def parse_csv(text: str) -> ParsedCsv:
    lines = text.splitlines()
    if not lines or not lines[0].strip():
        raise CsvFormatError("файл пустой или нет строки заголовка")
    reader = csv.reader(io.StringIO(text), delimiter=_detect_delimiter(lines[0]))
    header = next(reader)
    norm = [re.sub(r"\s+", "_", h.strip().lower()) for h in header]

    col: Dict[str, int] = {}
    for canon, names in ALIASES.items():
        for name in names:
            if name in norm:
                col[canon] = norm.index(name)
                break
    missing = [c for c in REQUIRED if c not in col]
    if missing:
        hints = "; ".join(f"{c}: {' / '.join(ALIASES[c])}" for c in missing)
        raise CsvFormatError(f"не найдены обязательные колонки. Допустимые названия: {hints}")

    out = ParsedCsv()
    seen_ids: Set[str] = set()
    for rownum, row in enumerate(reader, start=2):
        if not any(c.strip() for c in row):
            continue
        if rownum - 1 > MAX_ROWS:
            raise CsvFormatError(f"в файле больше {MAX_ROWS} строк")

        def cell(name: str) -> str:
            i = col.get(name)
            return row[i].strip() if i is not None and i < len(row) else ""

        try:
            src_raw, dst_raw = cell("from"), cell("to")
            if not src_raw or not dst_raw:
                raise ValueError("пустой идентификатор счёта")
            src, dst = to_token(src_raw), to_token(dst_raw)
            if src == dst:
                raise ValueError("отправитель и получатель совпадают")
            amount = _parse_amount(cell("amount"))
            ts = _parse_time(cell("timestamp"))
            from_bank, to_bank = _parse_bank(cell("from_bank")), _parse_bank(cell("to_bank"))
            channel = _parse_enum(Channel, cell("channel"), Channel.MIA_P2P, "channel")
            from_type = _parse_enum(AccountType, cell("from_type"), None, "from_type")
            to_type = _parse_enum(AccountType, cell("to_type"), None, "to_type")
            tx_id = cell("tx_id")
            if tx_id and tx_id in seen_ids:
                raise ValueError(f"повторяющийся tx_id '{tx_id}'")
            for h, bank in ((src, from_bank), (dst, to_bank)):
                known = out.accounts.get(h)
                if known is not None and known.bank_code != bank:
                    raise ValueError(f"счёт уже встречался в банке {known.bank_code.value}, а здесь указан {bank.value}")
        except ValueError as e:
            out.errors.append((rownum, str(e)))
            continue

        for h, bank, typ in ((src, from_bank, from_type), (dst, to_bank, to_type)):
            acc = out.accounts.get(h)
            if acc is None:
                out.accounts[h] = Account(account_hash=h, bank_code=bank, account_type=typ or AccountType.PERSONAL)
            elif typ is not None:
                acc.account_type = typ
        kwargs = {"tx_id": tx_id} if tx_id else {}
        if tx_id:
            seen_ids.add(tx_id)
        out.transactions.append(Transaction(
            timestamp=ts, from_hash=src, to_hash=dst, from_bank=from_bank, to_bank=to_bank,
            amount_mdl=amount, channel=channel, **kwargs,
        ))
    return out
