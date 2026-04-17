import numba
import numpy as np
import numpy.polynomial as np_poly

from .data_models import RootConvergenceMap


@numba.njit(fastmath={'nsz', 'arcp', 'contract', 'reassoc'}, inline='always')
def _eval_polynomial(coef_desc: np.ndarray, z: np.complex128) -> tuple[np.complex128, np.complex128]:
    result = 0 + 0j
    deriv = 0 + 0j
    for i in coef_desc:
        deriv = z * deriv + result
        result = z * result + i
    return result, deriv


@numba.njit(fastmath={'nsz', 'arcp', 'contract', 'reassoc'}, inline='always')
def _check_for_close_root(z: np.complex128, nroots, roots, tol2: float) -> int:
    best_idx = -1
    best_d2 = tol2
    for k in range(nroots):
        diff = roots[k] - z
        d2 = diff.real * diff.real + diff.imag * diff.imag
        if d2 < best_d2:
            best_d2 = d2
            best_idx = k
    return best_idx

@numba.njit(fastmath={'nsz', 'arcp', 'contract', 'reassoc'})
def _calc_newt_and_return_root_no_numba(
        z: np.complex128,
        poly_coef_desc: np.ndarray,
        roots: np.ndarray,
        iterations,
        tol=1e-6,
) -> int:
    for _ in range(iterations):
        f, f_prime = _eval_polynomial(poly_coef_desc, z)

        max_deriv_tolerance = 1e-14

        if f_prime.real * f_prime.real + f_prime.imag * f_prime.imag < max_deriv_tolerance * max_deriv_tolerance:
            return -1

        z = z - f/f_prime

        tol2 = tol * tol
        nroots = roots.shape[0]
        best_idx = _check_for_close_root(z, nroots, roots, tol2)
        if best_idx >= 0:
            return best_idx

    return -1


@numba.njit(fastmath={'nsz', 'arcp', 'contract', 'reassoc'})
def _apply_newton_numba(
        z_plane, poly_coef_desc: np.ndarray, roots, iterations
) -> np.typing.NDArray[np.int8]:

    rows, cols = z_plane.shape
    result = np.empty((rows, cols), dtype=np.int8)
    for i in numba.prange(rows):
        for j in range(cols):
            result[i, j] = _calc_newt_and_return_root_no_numba(
                z_plane[i, j], poly_coef_desc, roots, iterations
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
    result = _apply_newton_numba(z_plane, poly_coef_desc, roots, iterations)
    return RootConvergenceMap(data=result)

