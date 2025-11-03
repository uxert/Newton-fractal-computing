from newton_raphson import utils, launch_multiprocess
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
    sqrt_points_total = 6000
    sqrt_chunks_amount = 20
    if sqrt_points_total % sqrt_chunks_amount != 0:
        raise ValueError("sqrt_points_total must be divisible by sqrt_chunks_amount")
    sqrt_points_per_chunk = int(sqrt_points_total // sqrt_chunks_amount)
    try:
        b = time.perf_counter()
        chunks = utils.divide_complex_space(real_lower, real_upper, img_lower, img_upper, sqrt_points_per_chunk, sqrt_chunks_amount)
        e = time.perf_counter()
        print(f"Dividing into chunks took {e-b:.2f} seconds")
        b = time.perf_counter()
        result = launch_multiprocess.launch_parallel_pool(poly, chunks, n_workers=8)
        e = time.perf_counter()
        print(f"Computation and process overhead took {e-b:.2f} seconds")
    except Exception as e:
        print(f"There was an error during computation: {e}")
        raise
    try:
        b = time.perf_counter()
        filename = f"parallel_pool_{sqrt_points_total}.tiff"
        if result.size < 2**30:
            utils.visualize_np_array(result, filename)
        else:
            print(f"Resulting array has {result.size} elements, using tifffile")
            utils.visualize_np_array_to_tiff(result, filename)
        e = time.perf_counter()
        print(f"Saved {filename}, visualization took {e-b:.2f} seconds")
    except Exception as e:
        print(f"There was an error during visualization: {e}")
