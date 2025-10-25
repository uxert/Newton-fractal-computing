from newton_raphson import newton_raphson_compute, utils, launch_multiprocess
import numpy.polynomial
import time


if __name__ == "__main__":
    # example parallel execution
    # 3 + 5z + z^2 + 2z^4
    poly = numpy.polynomial.Polynomial((3, 5, 1, 0, 2))

    # parallel execution
    real_upper = 10
    real_lower = - real_upper
    img_upper = real_upper
    img_lower = - img_upper
    sqrt_points_per_chunk = 500
    sqrt_chunks_amount = 3
    b = time.perf_counter()
    chunks = utils.divide_complex_space(real_lower, real_upper, img_lower, img_upper, sqrt_points_per_chunk, sqrt_chunks_amount)
    e = time.perf_counter()
    print(f"Dividing into chunks took {e-b:.2f} seconds")
    b = time.perf_counter()
    result = launch_multiprocess.launch_parallel_fixed(poly, chunks)
    e = time.perf_counter()
    print(f"Computation and process overhead took {e-b:.2f} seconds")
    utils.visualize_np_array(result, "parallel_fixed.png")