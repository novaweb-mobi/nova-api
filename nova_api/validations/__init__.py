"""
Default validations for NovaAPI
"""
from typing import Any


def has_min_length(value: Any, *, min_length: int = 0) -> bool:
    """Checks whether the value has a minimum length of min_length

    :param value: The value to check if has minimum length
    :param min_length: The minimum length
    :return: Whether the value length is greater or equal to min_length
    """
    return len(value) >= min_length


def has_max_length(value: Any, *, max_length: int = 10) -> bool:
    """Checks whether the value has a maximum length of max_length

    :param value: The value to check if has maximum length
    :param max_length: The maximum length
    :return: Whether the value length is less or equal to max_length
    """
    return len(value) <= max_length


def is_less_than(value: Any, *, upper_bound: Any = 10) -> bool:
    """Checks whether the value is less than the upper_bound

    :param value: The value to check if is less than
    :param upper_bound: The upper bound
    :return: Whether the value is less than upper_bound
    """
    return value < upper_bound


def is_greater_than(value: Any, *, lower_bound: Any = 0) -> bool:
    """Checks whether the value is greater than the lower_bound

    :param value: The value to check if is greater than
    :param lower_bound: The lower bound
    :return: Whether the value is greater than lower_bound
    """
    return value > lower_bound


__all__ = ('has_min_length', 'has_max_length',
           'is_less_than', 'is_greater_than')
