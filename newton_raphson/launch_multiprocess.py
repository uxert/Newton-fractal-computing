from multiprocessing import Process, Queue, set_start_method, Pool, get_start_method
import numpy as np
from typing import List, Tuple
from math import sqrt
import sys
from tqdm import tqdm

from .newton_raphson_compute import calculate_newton_raphson
from .utils import combine_arrays_into_square

if get_start_method(allow_none=True) is None:
    set_start_method("spawn")  # Numpy and its threads go haywire when forking (which is default on UNIX, my machine)
# spawn is slower, but much safer. And let's be honest - process management will NOT be the bottleneck here

def newton_raphson_worker(mp_queue: Queue, worker_no: int, poly: np.polynomial.Polynomial, real_linspace, imaginary_linspace):
    try:
        result = calculate_newton_raphson(poly, real_linspace=real_linspace, imaginary_linspace=imaginary_linspace)
        if mp_queue is not None:
            mp_queue.put((worker_no, result), block=True)
            print(f"worker {worker_no} done!")
            sys.exit(0)  # explicitely exit, this should force all numpy/BLAS threads to terminate
        return worker_no, result
    except Exception as e:
        print(f"Worker {worker_no} failed: {e}")
        if mp_queue is not None:
            mp_queue.put((worker_no, f"ERROR: {e}"))
        raise

def launch_parallel_fixed(poly: np.polynomial.Polynomial, chunks: List[Tuple]) -> np.ndarray:
    """
    Allows to spawn multiple Processes, each doing calculate_newton_raphson on one chunk of complex space.
    The chunks must have "square" amount of elements

    """
    if sqrt(len(chunks)) != int(sqrt(len(chunks))):
        raise ValueError(f'chunks must be square, received {len(chunks)}')


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
    return combine_arrays_into_square(results)

def newton_raphson_worker_wrapper(args):
    return newton_raphson_worker(*args)

def launch_parallel_pool(poly: np.polynomial.Polynomial, chunks: List[Tuple], n_workers=4) -> np.ndarray:
    """
    Takes list of chunks and launches them in parallel using multiprocessing pool executor.
    Allows for better load balancing.

    """
    if sqrt(len(chunks)) != int(sqrt(len(chunks))):
        raise ValueError(f'chunks must be square, received {len(chunks)}')

    # None for the Queue
    tasks = [(None, worker_no, poly, chunk[0], chunk[1])
             for worker_no, chunk in enumerate(chunks)]

    with Pool(processes=n_workers) as pool:
        # results = pool.starmap(newton_raphson_worker, tasks)
        results = list(tqdm(pool.imap_unordered(newton_raphson_worker_wrapper, tasks, chunksize=32),
                            total=len(tasks)))
    if len(results) != len(chunks):
        raise RuntimeError(f'Something went horribly wrong - there were {len(chunks)} chunks, but {len(results)} results came back')

    results.sort(key=lambda x: x[0])  # Sort by task id to maintain order
    results = [pair[1] for pair in results]  # after sorting leave only the arrays
    return combine_arrays_into_square(results)


