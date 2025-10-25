"""This module contains things that are used by rest of the package"""

import numpy as np
from typing import List

def compare_with_values(values: List[complex], x: complex, epsilon=1e-4) -> int:
    """
    Compares provided number x with values from provided list. If x is close enough (denoted by epsilon)
    to any of the values, its index is returned (always returns index of the first close value).
    Returns -1 if x is not close to any number at all.
    """
    for i, root in enumerate(values):
        if np.isclose(root, x, atol=epsilon):
            return i
    return -1

