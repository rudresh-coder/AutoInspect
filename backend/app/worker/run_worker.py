from rq import SimpleWorker

from backend.app.worker.queue import (
    image_processing_queue,
    redis_connection,
)


if __name__ == "__main__":
    worker = SimpleWorker(
        [image_processing_queue],
        connection=redis_connection,
    )

    worker.work(with_scheduler=False)