from concurrent.futures import (
    CancelledError,
    Future,
)
from concurrent.futures.process import ProcessPoolExecutor
from multiprocessing import get_context

from .data_models import Task
from .distributed_worker import start_newton_raphson_worker
from .launch_multiprocess import newton_raphson_worker_local


# TODO: this will NOT work if separate processes use `entrypoints.py`. This requires some more complex IPC management if entrypoints concept is to stay this way
class EntrypointsManager:

    spawned_processes = []
    local_executor: ProcessPoolExecutor = None

    @classmethod
    def spawn_local_workers_pool(cls, workers_amount: int):
        ctx = get_context("spawn")
        cls.local_executor = ProcessPoolExecutor(max_workers=workers_amount, mp_context=ctx)

    @classmethod
    def submit_task_to_local_pool_nowait(cls, task: Task) -> Future | None:
        """If returns None, this means that local workers were not spawned"""
        if cls.local_executor is None:
            return None
        return cls.local_executor.submit(newton_raphson_worker_local, task)

    @classmethod
    def submit_task_to_local_pool_and_wait(cls, task: Task, *, timeout_secs: float = 15.):
        """If returns None, this means that task failed, possibly because workers were not spawned or timeout came"""
        try:
            future = cls.submit_task_to_local_pool_nowait(task)
            if future is None:
                return None
            return future.result(timeout=timeout_secs)
        except TimeoutError or CancelledError:
            return None



    @classmethod
    def spawn_one_dist_worker(cls):
        """
        This spawns DISTRIBUTED workers, that are working on Rabbit MQ queue.

        Even though using numpy/scipy etc. achieves some parallelism, one worker usually does not utilize more
        than 2-3 CPU cores. Maybe this will be optimized in the future. However, right now on 'cpu-rich' systems
        spawning more than one worker is recommended.
        """

        ctx = get_context("spawn")
        p = ctx.Process(target=start_newton_raphson_worker)
        cls.spawned_processes.append(p)
        p.start()

    @classmethod
    def kill_one(cls):
        """Does NOT join() the killed process, simply signals it to terminate"""
        if len(cls.spawned_processes) > 0:
            p = cls.spawned_processes.pop()
            p.terminate()

    @classmethod
    def kill_all_workers(cls):
        """
        Will join() to ensure all workers are actually dead.

        If you launched entrypoints (this module) from multiple processes, you need to call this method in ALL OF THEM
        to kill all the workers.
        """
        if cls.local_executor is not None:
            cls.local_executor.shutdown(wait=True, cancel_futures=True)
            cls.local_executor = None

        for p in cls.spawned_processes:
            p.terminate()

        for p in cls.spawned_processes:
            p.join()

    @classmethod
    def join_all_workers(cls):
        for p in cls.spawned_processes:
            p.join()
