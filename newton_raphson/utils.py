"""This module contains things that are used by rest of the package"""

import numpy as np
from typing import List, Tuple
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from PIL import Image
from math import sqrt
import tifffile


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
    if arr.size > 2**32 - 1:
        raise ValueError("Image array too large, PIL won't handle arrays bigger than 2**32... Use tifffile!")
    unique_vals = np.unique(arr[arr != -1])
    n_colors = len(unique_vals)
    if n_colors > 10:
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


def visualize_np_array_to_tiff(arr: np.ndarray, name="image.tif") -> None:
    """
    Visualizes numpy array containing non-negative integers (or value -1) using tifffile.
    Value -1 will always be visualized as black.
    Saves as RGB TIFF image.
    """
    unique_vals = np.unique(arr[arr != -1])
    n_colors = len(unique_vals)
    if n_colors > 10:
        raise ValueError(f"Too many unique values: {n_colors}. Maximum is 10 (and additionally value -1).")

    cmap = cm.get_cmap("tab10")
    # have to use np.uint16 for colormap. This is just the colormap, not the array with data which is still np.uint8
    colormap = np.zeros((256, 3), dtype=np.uint16)
    for i in range(1, 11):
        rgba = cmap(i - 1)  # this uses 0-9 indexing
        colormap[i, :] = (np.array(rgba[:3]) * 65535).astype(np.uint16)

    arr = arr + 1  # black becomes 0 instead of -1
    arr = np.astype(arr, np.uint8,copy=False)

    tifffile.imwrite(name,
                     arr,
                     photometric='palette',
                     colormap=colormap.T,  # tifffile expects (3, 256)
                     compression='lzma',
                     bigtiff=True)

def divide_complex_space(real_lower: float, real_upper: float, img_lower: float, img_upper: float,
                         N_points: int, sqrt_N_fragments: int, lazy=False) -> List[Tuple]:
    """
    Divide 2D complex space into chunks for parallel computation. The space will always be divided into "square" amount of chunks
    so that they can be later nicely aligned with np.block()
    :param N_points: is number of points PER FRAGMENT. So in total there will be N_points * sqrt_N_fragments**2 points!
    N_points is the value that one worker will receive at a time
    :param lazy: allows to control whether it calculates and returns linspaces, or arguments that need to be later passed to np.linspace()
    :returns: IF NOT LAZY: List of tuples, each tuple has two ndarrays - first one representing real numbers,
        second one representing imaginary numbers.
        IF LAZY: List of nested tuples. Each tuple has two elements - one for real numbers and one for imaginary numbers.
        Each element is a dict of keyword arguments, that need to be passed to np.linspace().
        Hint - pass them via unpacking with ** operator.
    """
    fragments = []
    if lazy is False:
        print("Dividing complex space using immediate evaluation.\n"
          "Consider using lazy evaluation if you are working with big images. Around 300k X 300k is when "
          "memory footprint of returned linspaces themselves (still 1D vectors!) becomes problematic.")
    if lazy is True:
        print("Dividing complex space using lazy evaluation.")

    for i in range(sqrt_N_fragments):
        for j in range(sqrt_N_fragments):
            # Calculate bounds for this fragment
            real_start = real_lower + i * (real_upper - real_lower) / sqrt_N_fragments
            real_end = real_lower + (i + 1) * (real_upper - real_lower) / sqrt_N_fragments

            img_start = img_lower + j * (img_upper - img_lower) / sqrt_N_fragments
            img_end = img_lower + (j + 1) * (img_upper - img_lower) / sqrt_N_fragments

            if lazy is False:
                # Create linspaces for this fragment
                # watch for endpoint=False, otherwise the chunks will overlap
                real_linspace = np.linspace(real_start, real_end, N_points, endpoint=False)
                img_linspace = np.linspace(img_start, img_end, N_points, endpoint=False)

                fragments.append((real_linspace, img_linspace))

            if lazy is True:
                # watch for endpoint=False, otherwise the chunks will overlap
                real_args = {"start": real_start, "stop": real_end, "num": N_points, "endpoint": False}
                img_args = {"start": img_start, "stop": img_end, "num": N_points, "endpoint": False}

                fragments.append((real_args, img_args))

    return fragments

def combine_arrays_into_square(results: List[np.ndarray]):
    """
    Takes N^2 arrays and combines them into N x N matrix.
    :raises ValueError: If all arrays are not the same size, are not 2D or are not square
    """
    for arr in results:
        if arr.shape != results[0].shape:
            raise ValueError("All arrays must have same shape")
        if arr.ndim != 2:
            raise ValueError("All arrays must have 2 dimensions")
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("All arrays must be square")
    n = int(sqrt(len(results)))
    grid = []
    for i in range(n):
        row = []
        for j in range(n):
            idx = i * n + j
            row.append(results[idx])
        grid.append(row)

    # Combine into single array
    big_array = np.block(grid)
    print(big_array.dtype)
    return big_array