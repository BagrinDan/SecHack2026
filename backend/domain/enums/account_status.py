from enum import Enum


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPECT = "SUSPECT"
    FROZEN = "FROZEN"
