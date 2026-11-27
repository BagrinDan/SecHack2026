from enum import Enum


class AppMode(str, Enum):
    """Источник данных: встроенный симулятор или загруженный CSV."""
    simulator = "simulator"
    csv = "csv"
