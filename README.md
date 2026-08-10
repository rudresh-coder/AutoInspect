# AutoInspect

## Explainable Asynchronous Vehicle Image Analysis System

AutoInspect is an asynchronous vehicle image analysis system that accepts vehicle images, processes them through a background analysis pipeline, and returns a structured inspection report.

The system combines image-quality analysis, vehicle registration plate detection and OCR, exact duplicate detection, perceptual similarity analysis, and explainable results.

---

# 1. Problem Statement

Vehicle images collected from the field may contain several problems, including:

- Blurry images
- Poor exposure or low-light images
- Low-contrast images
- Duplicate images
- Visually similar images
- Images with difficult-to-read registration plates
- Invalid or corrupted image files
- OCR results with low confidence

AutoInspect attempts to identify and report these issues through a structured asynchronous processing pipeline.

The goal is not to guarantee perfect computer-vision accuracy. Instead, the system is designed to provide measurable results, confidence information, and explanations so that uncertainty can be understood by the user.

---

# 2. Key Features

- Vehicle image upload
- JPEG, PNG, and WebP validation
- Unique processing ID generation
- Cloudflare R2 object storage
- Image metadata persistence
- Asynchronous background processing
- Redis-backed RQ job queue
- PostgreSQL persistence
- Image sharpness analysis
- Exposure analysis
- Contrast analysis
- Vehicle registration plate detection
- OCR-based registration number extraction
- OCR confidence scoring
- Exact duplicate detection using SHA-256
- Perceptual similarity analysis using pHash
- Structured analysis results
- Explainable processing results
- Processing status tracking
- Failure reason reporting
- Bounded background-job retries
- Frontend processing timeline
- Responsive React frontend
- Production deployment
---

# 3. System Architecture

AutoInspect uses a client-server architecture with asynchronous background processing.

```text
                         ┌─────────────────────┐
                         │      React UI       │
                         │                     │
                         │ Image Upload        │
                         │ Processing Timeline │
                         │ Inspection Report   │
                         └──────────┬──────────┘
                                    │
                                    │ REST API
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │                     │
                         │ Upload Endpoint     │
                         │ Status Endpoint     │
                         │ Validation          │
                         └──────┬───────┬──────┘
                                │       │
                         ┌──────┘       └──────────┐
                         ▼                         ▼
                ┌───────────────┐          ┌───────────────┐
                │  PostgreSQL   │          │     Redis     │
                │               │          │               │
                │ Image records │          │ RQ Queue      │
                │ Analysis data │          │ Job state      │
                └───────────────┘          └───────┬───────┘
                                                  │
                                                  ▼
                                      ┌─────────────────────┐
                                      │      RQ Worker      │
                                      │                     │
                                      │ Image Processing    │
                                      │ Quality Analysis    │
                                      │ Plate + OCR         │
                                      │ Duplicate Analysis  │
                                      └──────────┬──────────┘
                                                 │
                                                 │ Download image
                                                 ▼
                                      ┌─────────────────────┐
                                      │    Cloudflare R2    │
                                      │                     │
                                      │ Persistent Images   │
                                      └─────────────────────┘
                                                 │
                                                 │ Analysis results
                                                 ▼
                                      ┌─────────────────────┐
                                      │     PostgreSQL      │
                                      │                     │
                                      │ Analysis Results    │
                                      │ Processing Status    │
                                      └─────────────────────┘

```

# 4. Service Flow

The overall service flow is:

```text
User
 │
 │ Upload vehicle image
 ▼
React Frontend
 │
 │ POST /api/v1/images
 ▼
FastAPI
 │
 ├── Validate image type
 ├── Validate image readability
 ├── Generate processing ID
 ├── Store image in Cloudflare R2
 ├── Store metadata in PostgreSQL
 └── Enqueue background job
          │
          ▼
       Redis / RQ
          │
          ▼
       RQ Worker
          │
          ├── Download image from R2
          ├── Quality Analysis
          ├── Plate Detection
          ├── OCR
          ├── Exact Duplicate Detection
          ├── Perceptual Similarity
          └── Explanation Generation
          │
          ▼
       PostgreSQL
          │
          │ Store analysis results
          ▼
React Frontend
 │
 │ Poll processing status
 ▼
Inspection Report
```
---

# 5. Processing Flow

The analysis pipeline consists of five conceptual stages:

```text
01 IMAGE INGESTION
        │
        ▼
02 QUALITY ANALYSIS
        │
        ▼
03 PLATE + OCR
        │
        ▼
04 DUPLICATE ANALYSIS
        │
        ▼
05 INSPECTION REPORT
```

---

# 6. Asynchronous Processing

Image processing MUST NOT block the upload request.

The upload API follows this flow:

```text
POST /api/v1/images
        │
        ▼
Return 202 Accepted
        │
        ├── processing_id
        ├── status = pending
        ├── filename
        └── created_at
```

The actual image processing is performed by an RQ background worker.

The processing states are:

```text
pending
   │
   ▼
processing
   │
   ├──────────────► failed
   │
   ▼
completed
```

The frontend periodically requests the processing-status endpoint until the processing reaches either `completed` or `failed`.

---

# 7. Queue Strategy

Redis is used as the queue backend and RQ manages the background jobs.

The FastAPI application enqueues image-processing jobs instead of performing the complete analysis during the upload request.

```text
FastAPI
   │
   │ Enqueue job
   ▼
Redis
   │
   ▼
RQ Worker
   │
   ▼
Image Processing
```

# 8. Major Design Decisions

## FastAPI

FastAPI was selected for:

- Clear API definitions
- Automatic OpenAPI documentation
- Request validation
- Easy integration with Python image-processing libraries

## PostgreSQL

PostgreSQL stores image metadata, processing status, and analysis results so results remain available after background processing.

## Redis + RQ

Redis and RQ provide the asynchronous job-processing architecture.

The API returns a processing ID immediately, while the RQ worker processes images independently from the upload request.

## Cloudflare R2 Object Storage

Cloudflare R2 is used for persistent image storage.

The database stores the R2 object key rather than relying on local filesystem storage.

During processing, the worker temporarily downloads the image from R2, runs the analysis, and removes the temporary file afterward.

This allows persistent image storage to remain separate from application compute.

## HTTP Polling

The frontend polls:

```text
GET /api/v1/images/{processing_id}

# 9. Results API

The system exposes an API to retrieve the current processing state and final analysis.

```text
GET /api/v1/images/{processing_id}
```

The response contains the current processing status.

Once processing is completed, the response includes the analysis object.

---

# 10. API Examples

## Upload Image

### Endpoint

`POST /api/v1/images`

### Request

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/v1/images" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@sample-2.jpg;type=image/jpeg"
```

### Successful Response

**HTTP 202 Accepted**

```json
{
  "processing_id": "b3f2ddea-6f2d-4063-90dc-28ab540ba496",
  "status": "pending",
  "filename": "sample-2.jpg",
  "created_at": "2026-08-09T13:40:01.620678Z"
}
```

The API returns `202 Accepted` because processing is asynchronous.

---

## Get Processing Status

### Endpoint

`GET /api/v1/images/{processing_id}`

### Request

```bash
curl -X GET \
  "http://127.0.0.1:8000/api/v1/images/b3f2ddea-6f2d-4063-90dc-28ab540ba496" \
  -H "accept: application/json"
```

### Pending Response

**HTTP 200 OK**

```json
{
  "processing_id": "b3f2ddea-6f2d-4063-90dc-28ab540ba496",
  "filename": "sample-2.jpg",
  "status": "pending",
  "file_size": 409742,
  "width": 960,
  "height": 1280,
  "created_at": "2026-08-09T13:40:01.620678Z",
  "updated_at": "2026-08-09T13:40:01.620678Z",
  "processing_started_at": null,
  "processing_completed_at": null,
  "error_message": null,
  "analysis": null
}
```

### Completed Response

**HTTP 200 OK**

```json
{
  "processing_id": "b3f2ddea-6f2d-4063-90dc-28ab540ba496",
  "filename": "sample-2.jpg",
  "status": "completed",
  "file_size": 409742,
  "width": 960,
  "height": 1280,
  "created_at": "2026-08-09T13:40:01.620678Z",
  "updated_at": "2026-08-09T13:40:07.511730Z",
  "processing_started_at": "2026-08-09T13:40:01.637692Z",
  "processing_completed_at": "2026-08-09T13:40:07.511730Z",
  "error_message": null,
  "analysis": {
    "overall_score": 98.03,
    "quality_score": 98.03,
    "blur_score": 100,
    "exposure_score": 94.71,
    "contrast_score": 98.73,
    "plate_detected": true,
    "plate_text": "LAT131059115",
    "plate_confidence": 0.8048,
    "exact_duplicate": false,
    "duplicate_similarity": 100,
    "explanation": "Quality, plate, OCR, and duplicate analysis completed."
  }
}
```

---

## Unsupported Image Type

### Endpoint

`POST /api/v1/images`

### Example

Uploading a file with an unsupported media type, such as a text file, returns:

**HTTP 415 Unsupported Media Type**

```json
{
  "detail": {
    "code": "UNSUPPORTED_IMAGE_TYPE",
    "message": "Only JPEG, PNG, and WebP images are supported."
  }
}
```

---

## Unknown Processing ID

### Endpoint

`GET /api/v1/images/{processing_id}`

### Example

```bash
curl -X GET \
  "http://127.0.0.1:8000/api/v1/images/00000000-0000-0000-0000-000000000000" \
  -H "accept: application/json"
```

### Response

**HTTP 404 Not Found**

```json
{
  "detail": "Image processing ID not found"
}
```

---

# 11. Get Processing Status

The processing status can be retrieved using the processing ID returned by the upload endpoint.

### Endpoint

`GET /api/v1/images/{processing_id}`

The endpoint can return the following processing states:

- `pending` — The image has been accepted and is waiting for the background worker.
- `processing` — The background worker is currently analyzing the image.
- `completed` — Image analysis has finished successfully.
- `failed` — Image processing failed and an error message is available.

The frontend periodically polls this endpoint while processing is active.

The polling stops when the processing reaches either `completed` or `failed`.

### Processing Lifecycle

```text
Image Upload
     │
     ▼
  pending
     │
     ▼
 processing
     │
     ├──────────────► failed
     │
     ▼
 completed
```

---

# 12. Error Handling

The system handles invalid requests, unsupported or invalid image files, unknown processing IDs, and background-processing failures using structured error responses.

## Unsupported Image Type

Only JPEG, PNG, and WebP images are supported.

Uploading an unsupported file type returns:

**HTTP 415 Unsupported Media Type**

```json
{
  "detail": {
    "code": "UNSUPPORTED_IMAGE_TYPE",
    "message": "Only JPEG, PNG, and WebP images are supported."
  }
}
```

# 13. Persistence

AutoInspect uses PostgreSQL to persist image-processing metadata and analysis results.

Stored information includes:

- Processing ID
- Filename and file size
- Image dimensions
- Processing status and timestamps
- Error information
- Analysis results

Uploaded images are stored in **Cloudflare R2**, while metadata and analysis results are stored in **PostgreSQL**.

The processing ID links the uploaded image, R2 object, background-processing job, database record, and frontend status requests.

During processing, the RQ worker temporarily downloads the image from R2, performs the analysis, and removes the temporary file afterward.

---

# 14. Project Structure

```text
AutoInspect/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── images.py
│   │   │
│   │   ├── analysis/
│   │   │   ├── ocr.py
│   │   │   ├── pipeline.py
│   │   │   └── quality.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── image_service.py
│   │   │   └── storage.py
│   │   │
│   │   ├── worker/
│   │   │   ├── queue.py
│   │   │   ├── run_worker.py
│   │   │   └── tasks.py
│   │   │
│   │   └── main.py
│   │
│   ├── constraints.txt
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── PipelineTimeline.jsx
│   │
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── ...
│
├── tests/
│   ├── conftest.py
│   └── test_api.py
│
├── sample_images/
├── uploads/
│
├── alembic/
├── alembic.ini
├── docker-compose.yml
├── render.yaml
├── start.sh
├── .env.example
├── .gitignore
└── README.md
```
---

# 15. Running Instructions

## Prerequisites

The project requires:

- Python
- Node.js
- Docker
- Docker Compose

---

## Step 1 — Start Infrastructure

From the project root:

```bash
docker compose up -d
```

This starts the required PostgreSQL and Redis containers.

Verify the containers:

```bash
docker compose ps
```

---

## Step 2 — Start the Backend Worker

Activate the Python virtual environment.

Then run:

```bash
python -m backend.app.worker.run_worker
```

The worker should display a message similar to:

```text
Listening on image-processing...
```

Keep this terminal running.

---

## Step 3 — Start FastAPI

Open another terminal from the project root.

Run:

```bash
python -m uvicorn backend.app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger/OpenAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Step 4 — Start the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

## Running the Complete System

The application requires the following components to be running:

```text
Terminal 1
    │
    └── Docker Compose
          ├── PostgreSQL
          └── Redis

Terminal 2
    │
    └── RQ Worker
          └── image-processing queue

Terminal 3
    │
    └── FastAPI
          └── http://127.0.0.1:8000

Terminal 4
    │
    └── React + Vite
          └── http://localhost:5173
```

Once all four components are running, open the frontend in the browser and upload a supported vehicle image.

## Deployment Note

The frontend and FastAPI backend are deployed separately, while image processing is handled by an RQ worker.

Because the image-analysis workload is CPU/memory intensive, the background worker is currently run locally on the developer's machine rather than as a continuously running cloud worker. The deployed backend stores uploaded images in Cloudflare R2 and places processing jobs in Redis. The local RQ worker consumes these jobs, downloads the image from R2, performs the analysis, and saves the results to PostgreSQL.

Therefore, for the deployed application to process new images, the RQ worker must be running locally:

```bash
python -m backend.app.worker.run_worker
```
The worker must remain running while images are being processed.


### Also add the actual problem/solution

Since this was an important engineering decision, I recommend adding a very short section after it:

```markdown
## Deployment Resource Constraint

During deployment, running the image-processing worker in the cloud introduced memory/resource limitations because image analysis and OCR are CPU/memory intensive.

Instead of increasing the deployment resources, the architecture was adjusted to separate API hosting from background processing. Cloudflare R2 provides persistent image storage, Redis provides the job queue, and the worker can process jobs independently.

This allowed the deployed API and frontend to remain lightweight while the heavier image-processing workload is handled by the worker.

# 16. Environment Configuration

AutoInspect uses environment variables for database, Redis, and Cloudflare R2 configuration.

Create a `.env` file in the project root based on `.env.example`.

Example:

```env
DATABASE_URL=your_database_connection_string
REDIS_URL=your_redis_connection_string

R2_ENDPOINT_URL=your_r2_endpoint_url
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=your_r2_bucket_name
```

# 17. Testing

AutoInspect includes automated API tests using `pytest` and FastAPI's `TestClient`.

Tests use an isolated SQLite database and mock the background queue, allowing API behavior to be tested without PostgreSQL, Redis, or an active RQ worker.

## Test Coverage

The test suite covers:

- JPEG, PNG, and WebP uploads
- Processing ID generation
- Processing status retrieval
- Image metadata persistence
- Unsupported file types
- Invalid image content
- Missing image field
- Unknown processing IDs

## Running Tests

From the project root:

```bash
pytest -v
```


# 18. AI Usage Disclosure

AI tools were used during development as engineering assistants for architecture discussions, debugging, error analysis, documentation, and implementation guidance.

## Where AI Was Used

AI assistance was used for:

- Architecture and implementation discussions
- Debugging API, frontend, Redis/RQ, and deployment issues
- Reviewing errors and logs
- Frontend interaction and processing-state design
- Reviewing edge cases and error handling
- Documentation and engineering trade-offs

AI-generated suggestions were reviewed and adapted to match the actual project implementation.

## AI Limitations

AI suggestions were not always correct and sometimes required correction based on the actual project structure, API behavior, runtime logs, and deployment environment.

For example, the frontend's five-stage processing timeline is a UI representation, while the backend exposes overall states such as:

```text
pending
processing
completed
failed
```

# 19. Engineering Trade-offs

### Cloud Object Storage
Cloudflare R2 is used for persistent image storage instead of local storage. This improves reliability for the deployed API and background worker, but adds external storage configuration.

### Asynchronous Processing
Redis and RQ are used to process images in the background instead of blocking the upload request. This improves responsiveness but adds worker and queue infrastructure.

### HTTP Polling
The frontend uses HTTP polling for processing-status updates instead of WebSockets or SSE. This keeps the implementation simple but requires repeated status requests.

### CPU Processing
Image analysis runs on CPU to avoid GPU infrastructure and additional cost. The trade-off is slower processing for computationally intensive workloads.

### Bounded Retries
RQ jobs use bounded retries with progressive intervals (10, 30, and 60 seconds). This improves reliability while preventing indefinite retries.

### Limited Processing States
The backend exposes overall processing status, while the frontend presents the workflow through a five-stage pipeline. This simplifies the API while still providing visual progress.

### Single Worker
The current deployment uses a single RQ worker, which is sufficient for the current scale but limits concurrent processing. Horizontal worker scaling can be added later.

# 20. Improvements With More Time

With additional development time, the following improvements could be considered:

- More accurate license-plate detection
- Improved OCR preprocessing and recognition accuracy
- Better Indian number-plate format validation
- More robust screenshot and photo-of-photo detection
- Advanced image tampering and manipulation detection
- GPU acceleration for faster image processing
- WebSocket/SSE-based real-time processing updates
- Authentication and authorization
- Analysis history and user-specific inspection records
- Batch image processing
- Expanded integration and end-to-end test coverage
- More sophisticated retry classification
- Dead-letter queue handling for permanently failed jobs
- Advanced monitoring, alerting, and distributed tracing
- Rate limiting and additional API security controls
- Horizontal scaling of background workers
- Improved idempotency and duplicate-job handling
- More comprehensive validation using larger and more diverse real-world vehicle image datasets

# 21. Scalability Concerns

The current implementation is suitable for a local or small-scale deployment.

For a larger production system, the following areas would require attention.

## Worker Scaling

Multiple RQ workers could consume jobs from the processing queue concurrently.


                 Redis Queue
                      │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
        Worker 1   Worker 2   Worker 3


# 22. Failure Handling Concerns

Potential failures include:

- Worker, Redis, or database failures
- Corrupted or invalid images
- OCR or analysis failures
- Queue backlog or duplicate jobs
- Large image uploads

The application records failures using the `failed` processing state and error information.

RQ uses bounded retries with progressive intervals:

- Maximum retries: 3
- Intervals: 10, 30, and 60 seconds
- Maximum attempts: 4

The deployed system uses Redis, PostgreSQL, and Cloudflare R2. Future hardening could include dead-letter queues, worker monitoring, alerting, and distributed tracing.

# 23. Assumptions

The following assumptions were made during implementation:

1. Vehicle images are uploaded through the API as multipart form data.
2. Only JPEG, PNG, and WebP images are supported.
3. Uploaded images are persisted in configured object storage such as Cloudflare R2, while temporary local files may be used during analysis.
4. Image processing may take several seconds and therefore must not block the upload request.
5. OCR output is probabilistic and therefore must include confidence information.
6. A matching SHA-256 hash indicates an exact duplicate file.
7. Perceptual similarity is useful for identifying visually similar images even when their file contents differ.
8. The current system is deployed and demonstrates an end-to-end production-like architecture, but it is not intended to be a certified or production-grade vehicle-inspection system.
9. Perfect ML accuracy is not assumed.
10. Analysis results should communicate uncertainty instead of presenting uncertain predictions as guaranteed facts.

# 24. Bonus Features Implemented

The assignment lists several optional bonus areas.

AutoInspect includes the following additional capabilities:

- Dashboard-style inspection UI
- Confidence scoring
- Processing failure recovery
- Docker Compose setup
- Structured logging through application and worker logs
- Performance observation of asynchronous processing
- Responsive UI
- Automated API tests using pytest
- Isolated test database
- Mocked background queue during API testing
- Validation tests for supported and unsupported image formats
- Invalid image validation tests
- Processing ID and status endpoint tests
- Metadata persistence tests
- Bounded background-job retries
- Progressive retry backoff
- RQ scheduler support for delayed retries
- **Full production deployment of the application**
- **Deployed React frontend**
- **Deployed FastAPI backend**
- **Production PostgreSQL database**
- **Production Redis queue for background processing**
- **Cloudflare R2 integration for persistent image storage**
- **Production background image-processing workflow using RQ**

These automated tests and deployment capabilities are part of the current implementation, not future improvements.

## Production Deployment

AutoInspect has been deployed as a working production application.

### Frontend

The React + Vite frontend is deployed as a Render Static Site:

```text
https://autoinspect-frontend.onrender.com
```
# 25. Design Philosophy

The assignment emphasizes thoughtful engineering over unnecessary complexity.

AutoInspect therefore prioritizes:

- Clear separation between API and background processing
- Explicit processing states
- Structured persistence
- Explainable results
- Confidence-aware OCR
- Failure handling
- Simple and understandable infrastructure
- Practical trade-offs
- Debuggability
- Bounded and recoverable background processing
- Controlled retry behavior

The frontend intentionally uses a restrained visual design rather than relying on excessive colors or decorative effects.

The processing pipeline is presented visually to communicate the underlying architecture without pretending that the backend exposes telemetry that it does not actually provide.

# 26. Limitations

AutoInspect is a prototype automated inspection system and should not be considered a certified vehicle-inspection or legal number-plate verification system.

Key limitations include:

- OCR and plate-detection errors
- False duplicate matches or missed duplicates
- Sensitivity to image quality and viewing conditions
- CPU-based processing time
- Limited tampering detection
- Limited vehicle-specific validation
- Processing delays under heavy worker load

Results should therefore be treated as automated inspection signals rather than absolute ground truth.

# 27. Conclusion

AutoInspect is an asynchronous image-processing system combining REST APIs, Redis/RQ background jobs, PostgreSQL, Cloudflare R2, image analysis, OCR, and duplicate detection.

The project is deployed with a React + Vite frontend and FastAPI backend, providing an end-to-end workflow from image upload to inspection results.

The system is functional but remains a prototype rather than a certified vehicle-inspection or legal number-plate verification system.

Future improvements include better OCR and detection accuracy, worker scaling, authentication, rate limiting, advanced monitoring, real-time updates, and broader real-world testing.