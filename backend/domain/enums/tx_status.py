from enum import Enum


class TxStatus(str, Enum):
    OK = "OK"            # перевод проведён и попал в граф
    BLOCKED = "BLOCKED"  # отклонён автопредотвращением: отправитель или получатель заморожен, либо перевод создал алерт
