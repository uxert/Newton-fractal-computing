from dataclasses import dataclass

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