"""Zero-PII токенизация: счета хранятся только как токены.

ФИО, IDNP и реальные IBAN в системе не хранятся.
"""
import hashlib

# Соль фиксирована для прототипа (в проде — секрет в KMS, общий для банков-участников MIA).
HASH_SALT = "muletrace-md-2026"
HASH_LEN = 12


def tokenize(identifier: str) -> str:
    """Zero-PII токен: первые 12 символов SHA-256(salt + IBAN/телефон)."""
    return hashlib.sha256((HASH_SALT + identifier).encode("utf-8")).hexdigest()[:HASH_LEN]
