"""This module contains things that are used by rest of the package"""

import logging
from io import BytesIO
from typing import (
    List,
)

import matplotlib
import numpy as np
from matplotlib import colors
from PIL import Image

from newton_raphson.compute.data_models import (
    EagerComplexSpaceDivision,
    LazyComplexSpaceDivision,
    LinspaceKwargs,
    RootConvergenceMap,
)


logger = logging.getLogger(__name__)


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


def divide_complex_space(real_lower: float, real_upper: float, img_lower: float, img_upper: float,
                         N_points: int, sqrt_N_fragments: int, lazy=False) ->  EagerComplexSpaceDivision | LazyComplexSpaceDivision:
    """
    Divide 2D complex space into chunks for parallel computation. The space will always be divided into "square" amount of chunks
    so that they can be later nicely aligned with np.block()
    :param N_points: is number of points PER FRAGMENT. So in total there will be N_points * sqrt_N_fragments**2 points!
    N_points is the value that one worker will receive at a time
    :param lazy: allows to control whether it calculates and returns linspaces, or arguments that need to be later passed to np.linspace()
    :returns: IF NOT LAZY: EagerComplexSpaceDivision, which contains linspaces that can be used to construct a fragment
    of complex plane.
    IF LAZY: LazyComplexSpaceDivision, which contains kwargs to construct linspaces. Hint - pass them via unpacking (**)
    :raises: ValueError if sqrt_N_fragments is not positive
    """
    fragments = []
    if lazy is False:
        logger.info("Dividing complex space using immediate evaluation.\n"
          "Consider using lazy evaluation if you are working with big images. Around 300k X 300k is when "
          "memory footprint of returned linspaces themselves (still 1D vectors!) becomes problematic.")
    if lazy is True:
        logger.info("Dividing complex space using lazy evaluation.")

    if not sqrt_N_fragments or sqrt_N_fragments <= 0:
        raise ValueError("sqrt_N_fragments must be positive.")

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

            else:
                # watch for endpoint=False, otherwise the chunks will overlap
                real_args: LinspaceKwargs = {"start": real_start, "stop": real_end, "num": N_points, "endpoint": False}
                img_args: LinspaceKwargs = {"start": img_start, "stop": img_end, "num": N_points, "endpoint": False}
                fragments.append((real_args, img_args))

    if lazy is False:
        return EagerComplexSpaceDivision(data=fragments)
    else:
        return LazyComplexSpaceDivision(data=fragments)


def get_zxy_complex_space(z: int, x: float, y: float, n:int = 200, l: float = 5) -> tuple[np.ndarray, np.ndarray]:
    l /= 2**z  # higher zoom: smaller bounds
    l2 = l / 2
    start_x = x - l2
    end_x = x + l2
    start_y = y - l2
    end_y = y + l2

    real_linspace = np.linspace(start_x, end_x, n, endpoint=False)
    img_linspace = np.linspace(start_y, end_y, n, endpoint=False)

    # Task takes linspaces instead of z_plane
    # re, im = np.meshgrid(real_linspace, img_linspace)
    # z_plane = re + 1j * im

    return real_linspace, img_linspace

def get_zxy_complex_space_offset(
        z: int, x: int, y: int, n:int = 200, l: float = 1
    ) -> tuple[np.ndarray, np.ndarray]:
    """Returns coordinates ready for leaflet, where (x,y) is not center of the tile, but it's corner"""

    tile_l = l / (2 ** z)

    # X grows to the right
    start_x = -l / 2 + x * tile_l
    end_x = start_x + tile_l

    # Y in Leaflet grows downward, but imaginary axis usually grows upward
    start_y = -l / 2 + y * tile_l
    end_y = start_y + tile_l

    real_linspace = np.linspace(start_x, end_x, n, endpoint=False)
    img_linspace = np.linspace(start_y, end_y, n, endpoint=False)

    return real_linspace, img_linspace

def produce_png_buffer_from_rcm(rcm: RootConvergenceMap) -> BytesIO:
    data = rcm.data
    bounds = np.arange(-1.5, 10.5, 1)
    cmap = colors.ListedColormap(["black"] + list(matplotlib.colormaps.get_cmap("tab10").colors))
    norm = colors.BoundaryNorm(bounds, ncolors=cmap.N)
    rgba = (cmap(norm(data)) * 255).astype(np.uint8)

    image = Image.fromarray(rgba, mode="RGBA")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer
