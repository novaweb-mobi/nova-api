from typing import Any


def has_min_length(value: Any, *, min_length: int = 0) -> bool:
    return len(value) >= min_length


def has_max_length(value: Any, *, max_length: int = 10) -> bool:
    return len(value) <= max_length


def is_less_than(value: Any, *, upper_bound: Any = 10) -> bool:
    return value < upper_bound


def is_greater_than(value: Any, *, lower_bound: Any = 0) -> bool:
    return value > lower_bound


__all__ = ('has_min_length', 'has_max_length',
           'is_less_than', 'is_greater_than')
