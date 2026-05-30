import logging
import pickle

from .constants import amqp_url
from newton_raphson.compute.newton_raphson_compute import calculate_newton_raphson


# hardcoded so that logging sets up correctly even when launching this module directly (gets name __main__ then)
logger = logging.getLogger("newton_raphson.distributed.distributed_worker")

def start_newton_raphson_worker(
        tasks_queue: str = "tasks",
        tiles_queue: str = "tiles",
):
    """
    Worker that:
    1. reads tasks from `tasks` queue
    2. calculates Newton-Raphson roots
    3. puts results to `tiles` queue
    """

    try:
        import pika
        from pika.exceptions import AMQPConnectionError
    except ImportError:
        raise ImportError("To use distributed worker you need `pika`, install requirements/amqp.txt")

    try:
        connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
        channel = connection.channel()
    except AMQPConnectionError as e:
        logger.error(f"AMQPConnectionError when connecting to pika: {str(e)}")
        return

    # ensure queues exist
    channel.queue_declare(queue=tasks_queue, durable=True)
    channel.queue_declare(queue=tiles_queue, durable=True)

    # only one task per worker
    channel.basic_qos(prefetch_count=1)

    def on_task(ch, method, properties, body: bytes):

        worker_no, poly, real_linspace, imaginary_linspace = pickle.loads(body)

        try:
            logger.debug("Task start")
            result = calculate_newton_raphson(
                poly,
                real_linspace=real_linspace,
                imaginary_linspace=imaginary_linspace,
            )
            logger.debug("Task end")
            payload = (worker_no, result.data)
        except Exception as e:
            logger.error(f"Worker {worker_no} failed: {e}")
            payload = (worker_no, f"ERROR: {e}")
            # we deliberately do not kill the worker on the exception, but keep it working

        # instead of using mp_queue.put((worker_no, result)) it's basic_publish
        ch.basic_publish(
            exchange="",
            routing_key=tiles_queue,
            body=pickle.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),  # delivery_mode=2 means persistent message
        )


        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=tasks_queue, on_message_callback=on_task)
    logger.info("Newton Worker is waiting for tasks...")
    channel.start_consuming()

if __name__=="__main__":
    start_newton_raphson_worker()