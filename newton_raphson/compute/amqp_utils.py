from importlib.util import find_spec
from typing import TYPE_CHECKING

try:
    import pika
except ImportError:
    pika = None

def check_pika_lib_availability() -> bool:
    try:
        return find_spec("pika") is not None
    except RuntimeError:
        return False

if TYPE_CHECKING:
    import pika

def obtain_amqp_blocking_connection(amqp_url: str) -> "pika.BlockingConnection":
    if pika is None:
        raise ImportError("For amqp functionality `pika` is required. Install requirements/amqp.txt")

    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
    return connection


def obtain_amqp_channel(connection: "pika.BlockingConnection", queue_name: str, prefetch_count: int = 1):

    if pika is None:
        raise ImportError("For amqp functionality `pika` is required. Install requirements/amqp.txt")

    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=prefetch_count)
    return channel


