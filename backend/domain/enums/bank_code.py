from enum import Enum


class BankCode(str, Enum):
    MAIB = "MAIB"
    MICB = "MICB"
    VICTORIABANK = "VICTORIABANK"
    OTP = "OTP"
    FINCOMBANK = "FINCOMBANK"
