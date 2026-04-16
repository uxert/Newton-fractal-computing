import numba
import numpy as np
import numpy.polynomial as np_poly

from .data_models import RootConvergenceMap


@numba.njit
def _eval_polynomial(coef_desc: np.ndarray, z: np.complex128) -> np.complex128:
    result = 0 + 0j
    for i in coef_desc:
        result = z * result + i
    return result


@numba.njit
def _calc_newt_and_return_root_no_numba(
        z: np.complex128,
        poly_coef_desc: np.ndarray,
        deriv_coef_desc: np.ndarray,
        roots: np.ndarray,
        iterations,
        tol=1e-6,
) -> int:
    for _ in range(iterations):
        f = _eval_polynomial(poly_coef_desc, z)
        f_prime = _eval_polynomial(deriv_coef_desc, z)

        if np.abs(f_prime) < 1e-14:
            return -1

        z = z - f/f_prime
        distances = np.abs(roots - z)

        root_idx = int(np.argmin(distances))
        if distances[root_idx] < tol:
            return root_idx

    return -1


@numba.njit
def _apply_newton_numba(
        z_plane, poly_coef_desc: np.ndarray, deriv_coef_desc: np.ndarray, roots, iterations
) -> np.typing.NDArray[np.int8]:

    rows, cols = z_plane.shape
    result = np.empty((rows, cols), dtype=np.int8)
    for i in numba.prange(rows):
        for j in range(cols):
            result[i, j] = _calc_newt_and_return_root_no_numba(
                z_plane[i, j], poly_coef_desc, deriv_coef_desc, roots, iterations
            )

    return result


def calculate_newton_raphson(
        poly: np_poly.Polynomial,
        real_linspace,
        imaginary_linspace,
        iterations: int = 100,
) -> RootConvergenceMap:

    re, im = np.meshgrid(real_linspace, imaginary_linspace)
    z_plane = re + 1j * im

    deriv = poly.deriv()
    roots = poly.roots()
    poly_coef_desc = poly.coef[::-1]
    deriv_coef_desc = deriv.coef[::-1]
    result = _apply_newton_numba(z_plane, poly_coef_desc, deriv_coef_desc, roots, iterations)
    return RootConvergenceMap(data=result)

