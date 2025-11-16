import pickle
import pika
from constants import amqp_url

from newton_raphson.newton_raphson_compute import calculate_newton_raphson


def start_newton_raphson_worker(
        tasks_queue: str = "tasks",
        tiles_queue: str = "tiles",
):
    """
    Worker, który:
    - czyta zadania z kolejki `tasks`
    - liczy Newton-Raphson
    - wynik wrzuca do kolejki `tiles` jako (worker_no, result)
    """

    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
    channel = connection.channel()

    # Upewniamy się, że kolejki istnieją
    channel.queue_declare(queue=tasks_queue, durable=True)
    channel.queue_declare(queue=tiles_queue, durable=True)

    # Jeden task na raz na worker
    channel.basic_qos(prefetch_count=1)

    def on_task(ch, method, properties, body: bytes):
        # Oczekujemy, że w tasks jest:
        # pickle.dumps((worker_no, poly, real_linspace, imaginary_linspace))
        worker_no, poly, real_linspace, imaginary_linspace = pickle.loads(body)

        try:
            print("Task start")
            result = calculate_newton_raphson(
                poly,
                real_linspace=real_linspace,
                imaginary_linspace=imaginary_linspace,
            )
            print("Task end")
            payload = (worker_no, result)
        except Exception as e:
            print(f"Worker {worker_no} failed: {e}")
            # tak jak wcześniej: wrzucamy info o błędzie
            payload = (worker_no, f"ERROR: {e}")
            # w wersji rabbitowej NIE zabijamy workera, tylko lecimy dalej

        # zamiast mp_queue.put((worker_no, result))
        ch.basic_publish(
            exchange="",
            routing_key=tiles_queue,
            body=pickle.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),  # trwała wiadomość
        )

        # potwierdzamy, że task z `tasks` został obsłużony
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # Podpinamy callback i odpalamy konsumpcję
    channel.basic_consume(queue=tasks_queue, on_message_callback=on_task)
    print("[Newton worker] Waiting for tasks...")
    channel.start_consuming()

if __name__=="__main__":
    start_newton_raphson_worker()