from multiprocessing import Process, Queue, set_start_method, Pool, get_start_method
import queue
import numpy as np
from typing import List, Tuple
from math import sqrt
from tqdm import tqdm
import logging

from .newton_raphson_compute import calculate_newton_raphson
from .utils import combine_arrays_into_square

logger = logging.getLogger(__name__)

if get_start_method(allow_none=True) is None:
    set_start_method("spawn")  # Numpy and its threads go haywire when forking (which is default on UNIX, my machine)
# spawn is slower, but much safer. And let's be honest - process management will NOT be the bottleneck here

def newton_raphson_worker(mp_queue: Queue, worker_no: int, poly: np.polynomial.Polynomial, real_linspace, imaginary_linspace):
    try:
        result = calculate_newton_raphson(poly, real_linspace=real_linspace, imaginary_linspace=imaginary_linspace)
        if mp_queue is not None:
            try:
                mp_queue.put((worker_no, result), block=False)
            except queue.Full:
                logger.warning("Queue was full. This means your file-writer is not keeping up! Decrease compression")
                # Now do blocking put if needed
                mp_queue.put((worker_no, result), block=True)
            return None
        else:
            return worker_no, result
    except Exception as e:
        logger.error(f"Worker {worker_no} failed: {e}")
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
    Chunks need to be linspaces (this doesn't, and will not, allow for lazy chunking) - without using tiled writer your
    machine RAM will end long before you even notice memory footprint of calculating all chunks at once.

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

def _task_generator(queue, poly, chunks, used_type):
    if issubclass(used_type, np.ndarray):
        for worker_no, chunk in enumerate(chunks):
            yield queue, worker_no, poly, chunk[0], chunk[1]

    if issubclass(used_type, dict):
        for worker_no, chunk in enumerate(chunks):
            real_linspace = np.linspace(**chunk[0])
            imag_linspace = np.linspace(**chunk[1])
            yield queue, worker_no, poly, real_linspace, imag_linspace

def launch_parallel_pool_fragment_writing(poly: np.polynomial.Polynomial, chunks: List[Tuple], queue, n_workers=4):
    """
    :param chunks: Fragments of 2D complex space. There are 2 options. Option 1- these are Tuples with 2 elements, each
        is already computed linspace. Option 2 - these are tuples with 2 elements, each a dictionary with kwargs that are
        to be passed to np.linspace().  Option 2 is recommended as it allows to not compute (and store in memory) the
        linspaces until they are needed.
    :param queue: multiprocess Queue that will link producers (newton_raphson_worker) with consumer (tiled writer)
    :param n_workers: Amount of workers to spawn. Remember to always leave some CPU for writer process!
    :raises ValueError: If chunks are not in recognized format (described in this doc).
    :return:
    """
    if sqrt(len(chunks)) != int(sqrt(len(chunks))):
        raise ValueError(f'Amount of chunks must be square, received {len(chunks)}')
    used_type = type(chunks[0][0])
    if not issubclass(used_type, (dict, np.ndarray)):
        raise ValueError(f'chunks need to be either linspaces or dictionaries with kwargs, got {type(chunks[0][0])}')
    for chunk in chunks:
        if not isinstance(chunk, tuple):
            raise ValueError(f'Each chunk must be a tuple, received {type(chunk)}')
        if len(chunk) != 2:
            raise ValueError(f'Each chunk must be a tuple with 2 elements, received {len(chunk)}')
        if used_type != type(chunk[0]) or used_type != type(chunk[1]):
            raise ValueError(f'Chunk type not consistent')

    logger.info(f"Using generator to generate tasks on the fly - total expected task amount: {len(chunks):_}")
    tasks = _task_generator(queue, poly, chunks, used_type)
    logger.info(f"Launching pool with {n_workers} workers")

    with Pool(processes=n_workers) as pool:
        counter = 0
        with tqdm(total=len(chunks), desc="Calculations") as pbar:
            # iterating through imap_unordered should immediately consume results - no need to accumulate them
            for _ in pool.imap_unordered(newton_raphson_worker_wrapper, tasks, chunksize=32):
                counter += 1
                pbar.update(1)

    queue.put(None)  # receiving None will end file writer process
    if counter != len(chunks):
        raise RuntimeError(f'Something went wrong - there were {len(chunks)} chunks, but {counter} results came back')



