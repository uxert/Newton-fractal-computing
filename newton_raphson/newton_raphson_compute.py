import scipy
import numpy.polynomial as np_poly
import numpy as np
from typing import List
from itertools import product

from .utils import compare_with_values


def calc_newt_and_return_root_no(x: complex, poly: np_poly.Polynomial, deriv: np_poly.Polynomial,
                                 roots_list: List[complex], iterations: int = 50) -> int:
    try:
        root = scipy.optimize.newton(poly, x0=x, fprime=deriv, maxiter=iterations)
    except RuntimeError:
        return -1

    idx = compare_with_values(roots_list, root)
    return idx

def calculate_newton_raphson(poly: np_poly.Polynomial, N: int = 500,
                             real_lower: int = -5, real_upper: int = 5,
                             img_lower: int = -5, img_upper: int = 5, iterations: int = 50):
    """
    Function to visualize converge of Newton-Raphson algorithm for given fragment of complex space, defined by real upper/lower
    and img lower/upper bounds.
    :param poly: Polynomial used to compute Newton-Raphson. Can be max of degree 10
    :param N: How many points (along each axis!) should be generated. In total N^2 points will be checked
    :param iterations: maximum amount of Netwon-Raphson iterations performed for each seed value
    :return: 2D array of np.int8. Value on position [a, b] is index of the root that was result of performing Newton-Raphson
        with given polynomial and corresponding imaginary number (r + img*j) where r = real_lower + (real_upper - real_lower) * a / N
        and img = img_lower + (img_upper - img_lower) * b / N. Value -1 means the Newton-Raphson did not converge for seed (r + img*j)
    """
    if poly.degree() > 10:
        raise ValueError(f'polynomial must be degree 10 or lower, got degree {poly.degree()} instead')
    deriv = poly.deriv()
    roots = poly.roots()

    real = np.linspace(real_lower, real_upper, N)
    imag = np.linspace(img_lower, img_upper, N)
    re, im = np.meshgrid(imag, real)
    z_plane = re + 1j * im

    result = np.empty(shape=z_plane.shape, dtype=np.int8)
    for i, j in product(range(z_plane.shape[0]), range(z_plane.shape[1])):
        result[i,j] = calc_newt_and_return_root_no(z_plane[i, j], poly, deriv, roots, iterations=iterations)
        if i % (z_plane.shape[0]//50) == 0 and j==0:
            print("#", end="")
    print("\ndone!")

    return result
