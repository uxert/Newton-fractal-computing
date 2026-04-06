from multiprocessing import get_context

from .distributed_worker import start_newton_raphson_worker


# TODO: this will NOT work if separate processes use `entrypoints.py`. This requires some more complex IPC management if entrypoints concept is to stay this way
class EntrypointsManager:

    spawned_processes = []

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
        """Will join() to ensure all workers are actually dead"""
        for p in cls.spawned_processes:
            p.terminate()

        for p in cls.spawned_processes:
            p.join()

    @classmethod
    def join_all_workers(cls):
        for p in cls.spawned_processes:
            p.join()
