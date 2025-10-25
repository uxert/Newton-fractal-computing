from multiprocessing import Process, Queue, set_start_method
import numpy as np
from typing import List, Tuple
from math import sqrt
import sys

from .newton_raphson_compute import calculate_newton_raphson


def newton_raphson_worker(mp_queue: Queue, worker_no: int, poly: np.polynomial.Polynomial, real_linspace, imaginary_linspace):
    try:
        result = calculate_newton_raphson(poly, real_linspace=real_linspace, imaginary_linspace=imaginary_linspace)
        mp_queue.put((worker_no, result), block=True)
        print(f"worker {worker_no} done!")
        sys.exit(0)  # explicitely exit, this should force all numpy/BLAS threads to terminate
    except Exception as e:
        print(f"Worker {worker_no} failed: {e}")
        mp_queue.put((worker_no, f"ERROR: {e}"))
        raise

def launch_parallel_fixed(poly: np.polynomial.Polynomial, chunks: List[Tuple]) -> np.ndarray:
    """
    Allows to spawn multiple Processes, each doing calculate_newton_raphson on one chunk of complex space.
    The chunks must have "square" amount of elements

    """
    if sqrt(len(chunks)) != int(sqrt(len(chunks))):
        raise ValueError(f'chunks must be square, received {len(chunks)}')

    set_start_method("spawn")  # Numpy and its threads go haywire when forking (which is default on UNIX, my machine)
    # spawn is slower, but much safer. And let's be honest - process management will NOT be the bottleneck here

    mp_queue = Queue()
    processes = []
    results = []
    for worker_no, chunk in enumerate(chunks):
        real_linspace, imaginary_linspace = chunk
        p = Process(target=newton_raphson_worker, args=(mp_queue, worker_no, poly, real_linspace, imaginary_linspace))
        processes.append(p)
        p.start()

    for _ in range(len(processes)):
        results.append(mp_queue.get())

    for p in processes:
        p.join()



    if len(results) != len(chunks):
        raise RuntimeError(f'Something went horribly wrong - there were {len(chunks)} workers, but {len(results)} results came back')

    results.sort(key=lambda x: x[0])  # Sort by worker_id to maintain order
    results = [pair[1] for pair in results]  # after sorting leave only the arrays
    n = int(sqrt(len(results)))
    grid = []
    for i in range(n):
        row = []
        for j in range(n):
            idx = i * n + j
            row.append(results[idx])
        grid.append(row)

    # Combine into single array
    big_array = np.block(grid)
    print(big_array.dtype)
    return big_array


