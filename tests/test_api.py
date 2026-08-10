def test_upload_valid_jpeg(client, valid_jpeg):
    response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "test.jpg",
                valid_jpeg,
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert "processing_id" in data
    assert data["status"] == "pending"
    assert data["filename"] == "test.jpg"
    assert "created_at" in data


def test_upload_valid_png(client, valid_png):
    response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "test.png",
                valid_png,
                "image/png",
            )
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert "processing_id" in data
    assert data["status"] == "pending"
    assert data["filename"] == "test.png"


def test_upload_valid_webp(client, valid_webp):
    response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "test.webp",
                valid_webp,
                "image/webp",
            )
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert "processing_id" in data
    assert data["status"] == "pending"
    assert data["filename"] == "test.webp"


def test_upload_generates_unique_processing_ids(
    client,
    valid_jpeg,
):
    first_response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "first.jpg",
                valid_jpeg,
                "image/jpeg",
            )
        },
    )

    second_response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "second.jpg",
                valid_jpeg,
                "image/jpeg",
            )
        },
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 202

    first_id = first_response.json()["processing_id"]
    second_id = second_response.json()["processing_id"]

    assert first_id != second_id


def test_get_processing_status_after_upload(
    client,
    valid_jpeg,
):
    upload_response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "status-test.jpg",
                valid_jpeg,
                "image/jpeg",
            )
        },
    )

    assert upload_response.status_code == 202

    processing_id = upload_response.json()["processing_id"]

    status_response = client.get(
        f"/api/v1/images/{processing_id}"
    )

    assert status_response.status_code == 200

    data = status_response.json()

    assert data["processing_id"] == processing_id
    assert data["filename"] == "status-test.jpg"
    assert data["status"] == "pending"


def test_uploaded_image_metadata_is_persisted(
    client,
    valid_jpeg,
):
    upload_response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "metadata-test.jpg",
                valid_jpeg,
                "image/jpeg",
            )
        },
    )

    assert upload_response.status_code == 202

    processing_id = upload_response.json()["processing_id"]

    status_response = client.get(
        f"/api/v1/images/{processing_id}"
    )

    assert status_response.status_code == 200

    data = status_response.json()

    assert data["processing_id"] == processing_id
    assert data["filename"] == "metadata-test.jpg"
    assert data["file_size"] > 0
    assert data["width"] == 640
    assert data["height"] == 480
    assert data["status"] == "pending"
    assert data["created_at"] is not None
    assert data["updated_at"] is not None
    assert data["processing_started_at"] is None
    assert data["processing_completed_at"] is None
    assert data["error_message"] is None
    assert data["analysis"] is None


def test_upload_unsupported_file_type(client):
    response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "test.txt",
                b"This is not an image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415

    data = response.json()

    assert data["detail"]["code"] == "UNSUPPORTED_IMAGE_TYPE"

    assert (
        data["detail"]["message"]
        == "Only JPEG, PNG, and WebP images are supported."
    )


def test_upload_invalid_image_content(client):
    response = client.post(
        "/api/v1/images",
        files={
            "image": (
                "fake.jpg",
                b"This is not actually a JPEG image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"]["code"] == "INVALID_IMAGE"

    assert (
        data["detail"]["message"]
        == "The uploaded file is not a valid readable image."
    )


def test_missing_image_field(client):
    response = client.post(
        "/api/v1/images",
    )

    assert response.status_code == 422


def test_unknown_processing_id(client):
    processing_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(
        f"/api/v1/images/{processing_id}"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Image processing ID not found"
    )