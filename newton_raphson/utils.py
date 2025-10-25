"""This module contains things that are used by rest of the package"""

import numpy as np
from typing import List
import matplotlib.pyplot as plt
from PIL import Image


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

def visualize_np_array(arr: np.ndarray[int], name="image.png") -> None:
    """
    Visualizes numpy array containing non-negative integers (or value -1).
    Value -1 will always be visualized as black
    """
    unique_vals = np.unique(arr[arr != -1])
    n_colors = len(unique_vals)
    if n_colors > 20:
        raise ValueError(f"Too many unique values: {n_colors}. Maximum is 10 (and additionally value -1).")

    # unfortunately for PIL the colormap has to be RGB
    palette = [0, 0, 0] # Black for index 0

    tab10_colors = plt.cm.tab10.colors
    for i in range(n_colors):
        r, g, b = tab10_colors[i]
        palette.extend([int(r*255), int(g*255), int(b*255)])
    palette.extend([0] * (256 - n_colors - 1) * 3)  # PILs palette expects exactly 768 values: 256 colors x 3RGB channels
    indexed_arr = np.zeros_like(arr, dtype=np.uint8)
    for idx, val in enumerate(unique_vals):
        indexed_arr[arr == val] = idx + 1
    img = Image.fromarray(indexed_arr, mode='P')
    img.putpalette(palette)
    img.save(name)
