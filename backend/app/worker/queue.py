import redis
from rq import Queue

from backend.app.core.config import settings


redis_connection = redis.from_url(
    settings.redis_url,
)

image_processing_queue = Queue(
    "image-processing",
    connection=redis_connection,
)