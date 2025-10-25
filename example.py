"""This module is meant so serve as an introduction to creating the image itself"""

import numpy as np
import numpy.polynomial.polynomial as np_poly
from PIL import Image
import matplotlib.pyplot as plt
from typing import List
import scipy
from itertools import product


def simple_example():
    x = np.linspace(-250, 250, 15000)
    y = np.linspace(-250, 250, 15000)
    X, Y = np.meshgrid(x, y)
    color_values = X * Y

    # Visualize the array directly, seems to be working even for 15000 * 15000 points
    cmap = plt.cm.viridis
    color_norm = (color_values - color_values.min()) / (color_values.max() - color_values.min())
    img_array = (cmap(color_norm)[:, :, :3] * 255).astype(np.uint8)
    Image.fromarray(img_array).save('output.png')

def compare_with_roots(roots: List[complex], x: complex, epsilon=1e-4) -> int:
    """
    Compares provided value x with roots. If x is close enough (denoted by epsilon)
    to a root, root's index is returned. Returns -1 if is not close to any root at all
    """
    for i, root in enumerate(roots):
        if np.isclose(root, x, atol=epsilon):
            return i
    return -1

def calc_newt_and_return_root_no(x: complex, poly: np_poly.Polynomial, deriv: np_poly.Polynomial,
                                 roots_list: List[complex]) -> int:
    try:
        root = scipy.optimize.newton(poly, x0=x, fprime=deriv)
    except RuntimeError:
        return -1

    idx = compare_with_roots(roots_list, root)
    return idx

def real_example():
    # 1 - z + z^2 + z^5. Why 'z'? because it's complex time!
    # once again, I refer to https://www.youtube.com/watch?v=-RdOwhmqP5s
    poly = np_poly.Polynomial(coef=(1, -1, 1, 0, 0, 1))
    # standard polynomial differentiation, for complex works the same as for reals,
    # at least according to https://proofwiki.org/wiki/Derivative_of_Complex_Polynomial
    deriv = np_poly.Polynomial(coef=(-1,1,0,0,1))
    random_seed = -0.5 + 0.5j  # completely random, not copied from 3B1B example I pinky swear
    roots = poly.roots()
    print(f"roots:\n{roots}")
    # pycharm screams about wrong type, I don't know why, scipy docs say it can be complex
    # 3B1B chose example of a function and seed that do not converge :)
    try:
        test_newton = scipy.optimize.newton(poly, x0=random_seed, fprime=deriv, tol=1e-5)
        print(f"root returned by scipy.optimize.newton for seed {random_seed}: {test_newton}")
        print(f"This was expected as Newton-Raphson value does not converge for this seed and polynomial")
    except RuntimeError as e:
        print(f"Could not calculate Newton-Raphson, error occured: {str(e)}")

    # let's try something we know will converge for all points
    # (it can be checked by performing the algorithm on seed that is average of all 3 roots)
    # (this fact works only for cubic polynomials and is explained by 3B1B:
    # https://youtu.be/LqbZpur38nw?si=qyPM0j2mz9AN6Nsx&t=1038 )
    # maybe 5 + z + 2z^2 + z^3?
    poly = np_poly.Polynomial(coef=(5, 1, 2, 1))
    # 4z + 3z^2
    deriv = np_poly.Polynomial(coef=(1, 4, 3))
    roots = poly.roots()
    avg_seed = np.mean(roots)
    try:
        test_newton = scipy.optimize.newton(poly, x0=avg_seed, fprime=deriv, tol=1e-5)
        print("converges!")
    except RuntimeError as e:
        print(f"Could not calculate Newton-Raphson for poly {str(poly)}, error occured: {str(e)}")
    # correctly calculated, this means that for all points Newton-Raphson method will converge
    # 3B1B explained why this happens but I'm in no mental capacity to paraphrase this here

    N = 500
    a = 20
    real = np.linspace(-a, a, N)
    imag = np.linspace(-a, a, N)
    re, im = np.meshgrid(imag, real)
    z_plane = re + 1j * im
    print(z_plane.shape)
    exit(0)
    result = np.empty(shape=z_plane.shape)
    for i, j in product(range(z_plane.shape[0]), range(z_plane.shape[1])):
        result[i,j] = calc_newt_and_return_root_no(z_plane[i, j], poly, deriv, roots)
        if i % (z_plane.shape[0]//50) == 0 and j==0:
            print("#", end="")
    print("\ndone!")


    print(result)
    # Visualize the array directly, seems to be working even for 15000 * 15000 points
    cmap = plt.cm.viridis
    color_norm = (result - result.min()) / (result.max() - result.min())
    img_array = (cmap(color_norm)[:, :, :3] * 255).astype(np.uint8)
    Image.fromarray(img_array).save('output.png')

# simple_example()
real_example()
