from enum import Enum


class Scenario(str, Enum):
    """Сценарии симулятора атак; значения совпадают с ключами INJECTORS."""
    layered = "layered"
    business = "business"
    cycle = "cycle"
