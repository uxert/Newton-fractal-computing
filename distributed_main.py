import pickle
import time

import numpy as np
import numpy.polynomial
import pika
from pika.exceptions import AMQPConnectionError

from constants import amqp_url
from newton_raphson import (
    tiled_file_writer,
    utils,
)


def _task_generator(poly, chunks):
    for worker_no, chunk in enumerate(chunks):
        real_linspace = np.linspace(**chunk[0])
        imag_linspace = np.linspace(**chunk[1])
        yield worker_no, poly, real_linspace, imag_linspace


real_upper = 2
real_lower = - real_upper
img_upper = real_upper
img_lower = - img_upper
sqrt_points_total = 200
sqrt_chunks_amount = 20
polynomial_coefficients=(-16,0,0,0,15,0,0,0,1)
n_workers = 7


if __name__ == "__main__":
    poly = numpy.polynomial.Polynomial(coef=polynomial_coefficients)
    print(f"[Main] chosen polynomial: {poly}")
    if sqrt_points_total % sqrt_chunks_amount != 0:
        raise ValueError("sqrt_points_total must be divisible by sqrt_chunks_amount")
    sqrt_points_per_chunk = int(sqrt_points_total // sqrt_chunks_amount)
    print(f"[Main] sqrt_points_per_chunk: {sqrt_points_per_chunk}")

    filename = f"parallel_pool_{sqrt_points_total}.tiff"

    b = time.perf_counter()
    chunks = utils.divide_complex_space(real_lower, real_upper, img_lower, img_upper, sqrt_points_per_chunk, sqrt_chunks_amount, lazy=True)
    chunks = chunks.data
    e = time.perf_counter()
    print(f"[Main] Dividing into chunks took {e-b:.2f} seconds")
    tasks = _task_generator(poly, chunks)

    try:
        connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
        channel = connection.channel()
    except AMQPConnectionError as e:
        print(f"[Main]AMQPConnectionError when connecting to pika: {str(e)}")
        exit(0)


    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
    channel = connection.channel()

    # Ensure the queue exists
    channel.queue_declare(queue="tasks", durable=True)

    channel.basic_qos(prefetch_count=1)

    ttf = tiled_file_writer.TiledFileWriter(filename, None, sqrt_points_total, sqrt_chunks_amount, distributed=True)
    b = time.perf_counter()
    # launch_multiprocess.launch_parallel_pool_fragment_writing(poly, chunks,queue, n_workers=n_workers)
    for task in tasks:
        channel.basic_publish(
            exchange="",
            routing_key="tasks",
            body=pickle.dumps(task),
            properties=pika.BasicProperties(delivery_mode=2),  # delivery_mode=2 means persistent message
        )
    e = time.perf_counter()
    print(f"[Main] Sending tasks to rabbit queue took {e-b:.2f} seconds")
    ttf.start()

    # files bigger than 100k X 100k are not handled by tiffs that well and should be changed to deep zoom.
    # for that working on the compressed .h5 file is recommended
    if sqrt_points_total < 100_000:
        ttf.move_h5_to_tiff()
