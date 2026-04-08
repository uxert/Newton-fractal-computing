from dataclasses import dataclass
from typing import TypedDict

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Task:
    """
    This task passes linspaces directly. They are 1D vectors so these do not have much memory footprint, but care when
    using with big (as in, more than 100k px wide) images. For "normal" images this is completely negligible.

    In fact, on a local machine sending 10 and 10_000 numbers will probably take comparable amounts of time.
    """
    task_id: int
    poly: np.polynomial.Polynomial
    real_linspace: np.ndarray
    img_linspace: np.ndarray

@dataclass(frozen=True)
class RootConvergenceMap:
    data: NDArray[np.int8]

class LinspaceKwargs(TypedDict, total=True):
    start: float
    stop: float
    num: int
    endpoint: bool

@dataclass(frozen=True)
class LazyComplexSpaceDivision:
    """
    Each of the dicts represents kwargs to be passed to numpy.linspace(). First dict is for real numbers, second
    for imaginary numbers. Each tuple represents one chunk - one fragment of complex space
    """
    data: list[tuple[LinspaceKwargs, LinspaceKwargs]]

@dataclass(frozen=True)
class EagerComplexSpaceDivision:
    """
    Each of the NDArrays is one numpy.linspace(), which can be combined with numpy.meshgrid()
    to represent complex space. First NDArray is for real numbers, second for imaginary numbers.
    Each of the tuples represents one chunk - one fragment of complex space.
    """
    data: list[tuple[NDArray[float], NDArray[float]]]
