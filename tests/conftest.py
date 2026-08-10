import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import io
import shutil
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.images import router
from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.models.analysis import ImageAnalysis
from backend.app.models.image import Image


# Use an isolated in-memory SQLite database for tests.
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session")
def test_app():
    app = FastAPI()

    app.include_router(router)

    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(test_app, monkeypatch):
    upload_directory = tempfile.mkdtemp(
        prefix="autoinspect-tests-"
    )

    monkeypatch.setattr(
        settings,
        "upload_dir",
        upload_directory,
    )

    def fake_enqueue(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "backend.app.api.images.image_processing_queue.enqueue",
        fake_enqueue,
    )

    client = TestClient(test_app)

    yield client

    client.close()

    shutil.rmtree(
        upload_directory,
        ignore_errors=True,
    )


@pytest.fixture
def valid_jpeg():
    from PIL import Image as PILImage

    image = PILImage.new(
        "RGB",
        (640, 480),
        color="white",
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
    )

    buffer.seek(0)

    return buffer


@pytest.fixture
def valid_png():
    from PIL import Image as PILImage

    image = PILImage.new(
        "RGB",
        (640, 480),
        color="white",
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    buffer.seek(0)

    return buffer

@pytest.fixture
def valid_webp():
    from PIL import Image as PILImage

    image = PILImage.new(
        "RGB",
        (640, 480),
        color="white",
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="WEBP",
    )

    buffer.seek(0)

    return buffer