"""Симулятор трафика MIA: фоновый легитимный поток + 3 инъектора криминальных сценариев.

Все данные синтетические и Zero-PII: счета — только токены.
Инъекторы возвращают готовую цепочку транзакций с корректными (возрастающими) временными
метками. Сценарий «прошлого»: последняя транзакция = сейчас, начало отодвинуто назад на
длительность сценария — поэтому трассировка видит его целиком сразу после запуска.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from models import (
    Account,
    AccountStatus,
    AccountType,
    BankCode,
    Channel,
    Transaction,
    tokenize,
    utcnow,
)

BANKS: List[BankCode] = list(BankCode)

LEGIT_MIN_MDL = 50.0
LEGIT_MAX_MDL = 3500.0
POOL_SIZE = 200


class ScenarioResult(BaseModel):
    scenario: str
    root_tx_id: str
    transactions: List[Transaction] = Field(default_factory=list)
    new_accounts: List[Account] = Field(default_factory=list)


class Simulator:
    """Пул синтетических счетов и генератор транзакций."""

    def __init__(self, seed: Optional[int] = None, pool_size: int = POOL_SIZE) -> None:
        self.rng = random.Random(seed)
        self.accounts: Dict[str, Account] = {}
        self.legit_pool: List[str] = []  # только фоновые счета; счета сценариев в легитимный трафик не попадают
        self._pool_size = pool_size
        self.reset_pool()

    # ---- пул счетов ----
    def reset_pool(self) -> None:
        self.accounts.clear()
        self.legit_pool.clear()
        for i in range(self._pool_size):
            bank = BANKS[i % len(BANKS)]  # ровное распределение по 5 банкам
            acc_type = AccountType.BUSINESS if self.rng.random() < 0.1 else AccountType.PERSONAL
            self.legit_pool.append(self.new_account(bank, acc_type).account_hash)

    def new_account(self, bank: BankCode, account_type: AccountType = AccountType.PERSONAL) -> Account:
        # Токен строится от уникального синтетического идентификатора (имитация IBAN/телефона).
        acc = Account(
            account_hash=tokenize(f"SYN-{uuid.UUID(int=self.rng.getrandbits(128))}"),
            bank_code=bank,
            account_type=account_type,
        )
        self.accounts[acc.account_hash] = acc
        return acc

    def _legit_candidates(self) -> List[Account]:
        accs = (self.accounts[h] for h in self.legit_pool)
        return [a for a in accs if a.status != AccountStatus.FROZEN]

    # ---- легитимный трафик ----
    def legit_transaction(self) -> Transaction:
        pool = self._legit_candidates()
        src, dst = self.rng.sample(pool, 2)
        # Лог-нормальное распределение: много мелких сумм, редко крупные.
        amount = min(max(self.rng.lognormvariate(6.2, 0.9), LEGIT_MIN_MDL), LEGIT_MAX_MDL)
        return Transaction(
            from_hash=src.account_hash,
            to_hash=dst.account_hash,
            from_bank=src.bank_code,
            to_bank=dst.bank_code,
            amount_mdl=round(amount, 2),
            channel=self.rng.choice([Channel.MIA_P2P, Channel.MIA_QR]),
        )

    async def run_background(
        self, emit: Callable[[Transaction], Awaitable[None]], stop: Optional[asyncio.Event] = None
    ) -> None:
        """1–2 легитимные транзакции в секунду (пауза 0.5–1.0 с между транзакциями)."""
        while stop is None or not stop.is_set():
            await emit(self.legit_transaction())
            await asyncio.sleep(self.rng.uniform(0.5, 1.0))


# ---- хелперы инъекторов ----
class _Timeline:
    """Накапливает транзакции сценария с относительным временем (секунды от начала)."""

    def __init__(self, sim: Simulator) -> None:
        self.sim = sim
        self.items: List[tuple] = []  # (t_sec, src, dst, amount, channel)

    def tx(self, t: float, src: Account, dst: Account, amount: float, channel: Channel = Channel.MIA_P2P) -> None:
        self.items.append((t, src, dst, round(amount, 2), channel))

    def build(self, name: str, new_accounts: List[Account]) -> ScenarioResult:
        self.items.sort(key=lambda it: it[0])
        duration = self.items[-1][0]
        start = utcnow() - timedelta(seconds=duration)
        txs = [
            Transaction(
                timestamp=start + timedelta(seconds=t),
                from_hash=s.account_hash,
                to_hash=d.account_hash,
                from_bank=s.bank_code,
                to_bank=d.bank_code,
                amount_mdl=amt,
                channel=ch,
            )
            for t, s, d, amt, ch in self.items
        ]
        return ScenarioResult(scenario=name, root_tx_id=txs[0].tx_id, transactions=txs, new_accounts=new_accounts)


def _split(rng: random.Random, total: float, parts: int, lo: float, hi: float) -> List[float]:
    """Делит сумму на `parts` частей в [lo, hi]; остаток добавляется к последней, если влезает."""
    for _ in range(100):
        cuts = sorted(rng.uniform(0.3, 1.0) for _ in range(parts))
        weights = [c for c in cuts]
        s = sum(weights)
        chunks = [round(total * w / s, 2) for w in weights]
        if all(lo <= c <= hi for c in chunks):
            return chunks
    return [round(total / parts, 2)] * parts


# ---- инъекторы сценариев ----
def inject_layered_mule_chain(sim: Simulator) -> ScenarioResult:
    """Жертва (MAIB) → мошенник G1 (MICB) → G2 (MAIB/OTP/VICTORIABANK) → G3 → G4 (дробление 4–8 тыс. MDL)."""
    rng = sim.rng
    new: List[Account] = []

    def mk(bank: BankCode) -> Account:
        a = sim.new_account(bank)
        new.append(a)
        return a

    tl = _Timeline(sim)
    victim = mk(BankCode.MAIB)
    g1 = mk(BankCode.MICB)
    tl.tx(0, victim, g1, 48_000, Channel.MIA_P2P)

    # G2: за 3 минуты дробим на 3 счёта (MAIB, OTP, VICTORIABANK), ~4% комиссия мошенника.
    g2_banks = [BankCode.MAIB, BankCode.OTP, BankCode.VICTORIABANK]
    g2_total = 48_000 * 0.96
    g2_amounts = _split(rng, g2_total, 3, 9_000, 20_000)
    g2: List[tuple] = []
    for bank, amt in zip(g2_banks, g2_amounts):
        acc = mk(bank)
        t = rng.uniform(40, 180)  # внутри 3 минут от первой транзакции
        tl.tx(t, g1, acc, amt)
        g2.append((acc, amt, t))

    # G3: каждый G2 за 2–5 мин пересылает остаток на два счёта (другие банки).
    g3: List[tuple] = []
    for acc, amt, t0 in g2:
        parts = _split(rng, amt * 0.97, 2, 3_000, 14_000)
        for amt3 in parts:
            bank = rng.choice([b for b in BANKS if b != acc.bank_code])
            dst = mk(bank)
            t = t0 + rng.uniform(120, 300)
            tl.tx(t, acc, dst, amt3)
            g3.append((dst, amt3, t))

    # G4: крупные суммы (>8 тыс.) дробятся на переводы по 4–8 тыс. MDL, мелкие уходят целиком.
    for acc, amt, t0 in g3:
        amt_out = amt * 0.98
        if amt_out >= 8_000:
            chunks = _split(rng, amt_out, 2, 4_000, 8_000)
        else:
            chunks = [amt_out]
        for amt4 in chunks:
            bank = rng.choice([b for b in BANKS if b != acc.bank_code])
            dst = mk(bank)
            tl.tx(t0 + rng.uniform(60, 240), acc, dst, amt4)

    return tl.build("layered", new)


def inject_business_mule_ring(sim: Simulator) -> ScenarioResult:
    """6 счетов из разных банков → BUSINESS-счёт в MAIB → быстрый вывод на FINCOMBANK и OTP."""
    rng = sim.rng
    new: List[Account] = []

    def mk(bank: BankCode, t: AccountType = AccountType.PERSONAL) -> Account:
        a = sim.new_account(bank, t)
        new.append(a)
        return a

    tl = _Timeline(sim)
    hub = mk(BankCode.MAIB, AccountType.BUSINESS)
    # 6 отправителей: все 5 банков + ещё один случайный; суммы нетипичные для P2P (не круглые, 6–15 тыс.).
    banks = list(BANKS) + [rng.choice(BANKS)]
    rng.shuffle(banks)
    total_in = 0.0
    last_in = 0.0
    for i, bank in enumerate(banks):
        sender = mk(bank)
        amt = round(rng.uniform(6_300, 14_900), 2)
        t = i * rng.uniform(25, 50)
        tl.tx(t, sender, hub, amt, Channel.MIA_QR if i % 2 else Channel.MIA_P2P)
        total_in += amt
        last_in = max(last_in, t)

    # Быстрый вывод: через 1–3 минуты после последнего поступления, на 2 конечных счёта.
    out_total = total_in * 0.97
    share = rng.uniform(0.45, 0.55)
    tl.tx(last_in + rng.uniform(60, 120), hub, mk(BankCode.FINCOMBANK), out_total * share)
    tl.tx(last_in + rng.uniform(120, 180), hub, mk(BankCode.OTP), out_total * (1 - share))
    return tl.build("business", new)


def inject_test_and_cycle(sim: Simulator) -> ScenarioResult:
    """Тест 15 MDL → через 1 мин 35 000 MDL → кольцо из 4 счетов в разных банках."""
    rng = sim.rng
    new: List[Account] = []
    banks = rng.sample(BANKS, 4)
    ring = []
    for b in banks:
        a = sim.new_account(b)
        new.append(a)
        ring.append(a)

    tl = _Timeline(sim)
    a, b = ring[0], ring[1]
    tl.tx(0, a, b, 15)          # тестовый микроперевод
    tl.tx(60, a, b, 35_000)     # через 1 минуту — крупная сумма
    # Прогон по кольцу a→b→c→d→a, два круга, каждый переход чуть уменьшает сумму.
    amount = 35_000.0
    t = 60.0
    hops = [(ring[1], ring[2]), (ring[2], ring[3]), (ring[3], ring[0]),
            (ring[0], ring[1]), (ring[1], ring[2]), (ring[2], ring[3]), (ring[3], ring[0])]
    for src, dst in hops:
        t += rng.uniform(40, 90)
        amount *= 0.995
        tl.tx(t, src, dst, amount)
    return tl.build("cycle", new)


INJECTORS = {
    "layered": inject_layered_mule_chain,
    "business": inject_business_mule_ring,
    "cycle": inject_test_and_cycle,
}
