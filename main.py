from newton_raphson import newton_raphson_compute, utils
import numpy.polynomial
import time


if __name__ == "__main__":
    # example execution
    # 3 + 5z + z^2 + 2z^4
    poly = numpy.polynomial.Polynomial((3, 5, 1, 0, 2))
    begin_time = time.perf_counter()
    result = newton_raphson_compute.calculate_newton_raphson(poly, N=1000, real_lower=-2, real_upper=8, img_lower=-2, img_upper=8)
    end_time = time.perf_counter()
    print(f"Calculation took {end_time - begin_time:.5f} seconds.")
    begin_time = time.perf_counter()
    utils.visualize_np_array(result, name="image2.png")
    end_time = time.perf_counter()
    print(f"Visualization and image saving took {end_time - begin_time:.5f} seconds.")