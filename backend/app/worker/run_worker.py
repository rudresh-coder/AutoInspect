from rq import SimpleWorker

from backend.app.worker.queue import redis_connection


if __name__ == "__main__":
    worker = SimpleWorker(
        ["image-processing"],
        connection=redis_connection,
    )

    worker.work()