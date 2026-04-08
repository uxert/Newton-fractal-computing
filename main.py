import multiprocessing
import time

import numpy.polynomial

from newton_raphson import (
    launch_multiprocess,
    tiled_file_writer,
    utils,
)


real_upper = 10
real_lower = - real_upper
img_upper = real_upper
img_lower = - img_upper
sqrt_points_total = 10_000
sqrt_chunks_amount = 100
polynomial_coefficients=(-16,0,0,0,15,0,0,0,1)
n_workers = 7

if __name__ == "__main__":
    poly = numpy.polynomial.Polynomial(coef=polynomial_coefficients)
    print(f"[Main] chosen polynomial: {poly}")
    if sqrt_points_total % sqrt_chunks_amount != 0:
        raise ValueError("sqrt_points_total must be divisible by sqrt_chunks_amount")
    sqrt_points_per_chunk = int(sqrt_points_total // sqrt_chunks_amount)
    print(f"[Main] sqrt_points_per_chunk: {sqrt_points_per_chunk}. Empirically it seems that values like 125 work well. "
          f"Settings this value too big or too small will cause the program to slow down massively")

    filename = f"parallel_pool_{sqrt_points_total}.tiff"
    manager = multiprocessing.Manager()
    queue = manager.Queue(maxsize=100)  # really small - if the file writer is not keeping up this will fill almost instantly
    try:
        b = time.perf_counter()
        chunks = utils.divide_complex_space(real_lower, real_upper, img_lower, img_upper, sqrt_points_per_chunk, sqrt_chunks_amount, lazy=True)
        chunks = chunks.data
        e = time.perf_counter()
        print(f"[Main] Dividing into chunks took {e-b:.2f} seconds")
        b = time.perf_counter()
        ttf = tiled_file_writer.TiledFileWriter(filename, queue, sqrt_points_total, sqrt_chunks_amount)
        ttf.start()
        launch_multiprocess.launch_parallel_pool_fragment_writing(poly, chunks,queue, n_workers=n_workers)
        e = time.perf_counter()
        print(f"[Main] Computation and process overhead took {e-b:.2f} seconds")
    except Exception as e:
        print(f"[Main] There was an error during computation: {e}")
        raise
    # files bigger than 100k X 100k are not handled by tiffs that well and should be changed to deep zoom.
    # for that working on the compressed .h5 file is recommended
    if sqrt_points_total < 100_000:
        ttf.move_h5_to_tiff()
