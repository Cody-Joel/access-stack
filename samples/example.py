#!/usr/bin/env python3
"""
example.py — Sample Python code for the File Reader tool to display.

This file demonstrates a simple Python module with functions,
type hints, and docstrings.
"""

import math
from typing import List, Optional


def calculate_mean(values: List[float]) -> Optional[float]:
    """
    Calculate the arithmetic mean of a list of numbers.

    Args:
        values: List of numeric values

    Returns:
        The mean, or None if list is empty

    Example:
        >>> calculate_mean([1, 2, 3, 4, 5])
        3.0
    """
    if not values:
        return None
    return sum(values) / len(values)


def calculate_std_dev(values: List[float]) -> Optional[float]:
    """
    Calculate the standard deviation of a list of numbers.

    Uses the sample standard deviation formula (n-1 denominator).
    """
    if len(values) < 2:
        return None

    mean = calculate_mean(values)
    if mean is None:
        return None

    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


if __name__ == "__main__":
    # Example usage
    data = [10, 20, 30, 40, 50]
    print(f"Data: {data}")
    print(f"Mean: {calculate_mean(data)}")
    print(f"Std Dev: {calculate_std_dev(data)}")
