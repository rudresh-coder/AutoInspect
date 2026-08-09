from fastapi import FastAPI
from sqlalchemy import text

import redis

from backend.app.api.images import router as images_router
from backend.app.core.config import settings
from backend.app.core.database import Base, engine
from backend.app.models.image import Image


app = FastAPI(
    title=settings.app_name,
    description="Explainable asynchronous vehicle image analysis pipeline",
    version="1.0.0",
)


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


app.include_router(images_router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "running",
    }


@app.get("/health")
def health():
    health_status = {
        "status": "ok",
        "service": settings.app_name,
        "dependencies": {
            "database": "unknown",
            "redis": "unknown",
        },
    }

    # Check PostgreSQL
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        health_status["dependencies"]["database"] = "healthy"

    except Exception:
        health_status["status"] = "degraded"
        health_status["dependencies"]["database"] = "unhealthy"

    # Check Redis
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()

        health_status["dependencies"]["redis"] = "healthy"

    except Exception:
        health_status["status"] = "degraded"
        health_status["dependencies"]["redis"] = "unhealthy"

    return health_status