import logging
import queue
from math import sqrt
from multiprocessing import (
    get_start_method,
    Pool,
    Queue,
    set_start_method,
)
from typing import (
    List,
    Tuple,
)

import numpy as np
from tqdm import tqdm

from .data_models import (
    RootConvergenceMap,
    Task,
)
from .newton_raphson_compute_numba import calculate_newton_raphson


logger = logging.getLogger(__name__)

if get_start_method(allow_none=True) is None:
    set_start_method("spawn")  # Numpy and its threads go haywire when forking (which is default on UNIX, my machine)


# spawn is slower, but much safer. And let's be honest - process management will NOT be the bottleneck here

def newton_raphson_worker(
        mp_queue: Queue,
        worker_no: int,
        poly: np.polynomial.Polynomial,
        real_linspace,
        imaginary_linspace,
):
    try:
        result = calculate_newton_raphson(poly, real_linspace=real_linspace, imaginary_linspace=imaginary_linspace)
        if mp_queue is not None:
            try:
                mp_queue.put((worker_no, result.data), block=False)
            except queue.Full:
                logger.warning("Queue was full. This means your file-writer is not keeping up! Decrease compression")
                # Now do blocking put if needed
                mp_queue.put((worker_no, result.data), block=True)
            return None
        else:
            return worker_no, result.data
    except Exception as e:
        logger.error(f"Worker {worker_no} failed: {e}")
        if mp_queue is not None:
            mp_queue.put((worker_no, f"ERROR: {e}"))
        raise

def newton_raphson_worker_local(task: Task) -> Tuple[int, RootConvergenceMap] | None:
    """
    Worker that is meant to be launched via process pool. No queues, simply returns the result after it's done.
    Returns None if task failed
    """
    try:
        result = calculate_newton_raphson(
            poly=task.poly,
            real_linspace=task.real_linspace,
            imaginary_linspace=task.img_linspace,
        )
        return task.task_id, result
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        return None


def newton_raphson_worker_wrapper(args):
    return newton_raphson_worker(*args)


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



