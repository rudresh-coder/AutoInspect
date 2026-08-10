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
- Local image storage
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
- Frontend processing timeline
- Failed-upload recovery
- Responsive React frontend

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
                         └──────────┬──────────┘
                                    │
                      ┌─────────────┴─────────────┐
                      │                           │
                      ▼                           ▼
              ┌───────────────┐          ┌───────────────┐
              │  PostgreSQL   │          │     Redis     │
              │               │          │               │
              │ Image records │          │ RQ Queue      │
              │ Analysis data │          │ Job state     │
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
                                                 ▼
                                      ┌─────────────────────┐
                                      │ Analysis Result     │
                                      │                     │
                                      │ Quality             │
                                      │ OCR                 │
                                      │ Duplicates          │
                                      │ Explanation         │
                                      └─────────────────────┘

---

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
 ├── Store image
 ├── Store metadata
 └── Enqueue background job
          │
          ▼
       Redis / RQ
          │
          ▼
       RQ Worker
          │
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

Redis is used as the queue backend and RQ is used to manage background jobs.

The FastAPI application does not perform the complete image-analysis workload during the upload request.

Instead:

```text
FastAPI
   │
   │ enqueue job
   ▼
Redis
   │
   ▼
RQ Worker
   │
   ▼
Image Processing
```

This separation provides several benefits:

- The upload API responds quickly.
- CPU-intensive processing does not block HTTP requests.
- Processing can be handled independently by workers.
- The architecture can be extended to multiple workers.
- Queue-based processing provides a foundation for scaling.

The current implementation uses the `image-processing` queue.

# 8. Major Design Decisions

## FastAPI

FastAPI was selected for the backend because it provides:

- Clear API definitions
- Automatic OpenAPI documentation
- Request validation
- Good support for asynchronous/background-oriented applications
- Straightforward integration with Python image-processing libraries

---

## PostgreSQL

PostgreSQL is used for persistent application data.

It stores image metadata and analysis information so that processing results remain available after the background job finishes.

---

## Redis + RQ

Redis and RQ were selected for asynchronous job processing.

The main reason for this choice was simplicity while still demonstrating a real queue-based architecture.

The assignment allows different queue technologies and emphasizes engineering reasoning over a specific technology choice.

---

## Local File Storage

Uploaded images are currently stored locally.

This keeps the implementation simple and appropriate for a take-home assignment.

A production deployment could replace local storage with an object-storage system such as Amazon S3 or another cloud storage service.

---

## Polling for Processing Status

The frontend polls:

```text
GET /api/v1/images/{processing_id}
```

while processing is active.

Polling was chosen because it is simple to implement and sufficient for the current scale.

A production system with large numbers of concurrent users could use WebSockets or Server-Sent Events for more efficient real-time status updates.

---

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

The system handles invalid requests, invalid image files, unknown processing IDs, and background-processing failures using structured error responses.

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

The application uses PostgreSQL to persist image processing information.

Stored information includes:

- Processing ID
- Filename
- File size
- Image dimensions
- Processing status
- Creation timestamp
- Updated timestamp
- Processing start timestamp
- Processing completion timestamp
- Error message
- Analysis results

The database allows the application to retrieve processing results after the background job has completed.

Image files themselves are currently stored locally, while their metadata and analysis results are persisted in PostgreSQL.

The processing ID acts as the identifier connecting the uploaded image, background-processing job, database record, and frontend status requests.

---

# 14. Project Structure

```text
AutoInspect/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── analysis/
│       ├── core/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       └── worker/
│
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── hooks/
│       ├── App.jsx
│       ├── App.css
│       └── PipelineTimeline.jsx
│
├── sample_images/
├── uploads/
├── docker-compose.yml
├── alembic.ini
├── .env.example
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

# 16. Environment Configuration

The application uses environment variables for runtime configuration.

Create a `.env` file in the project root based on `.env.example`.

The environment configuration contains values required for connecting the application to its dependencies, including:

- PostgreSQL database configuration
- Redis connection configuration
- Application configuration

Example structure:

```env
DATABASE_URL=your_database_connection_string
REDIS_URL=your_redis_connection_string
```

Environment-specific values should be stored in environment variables rather than hard-coded into source code.

Secrets, passwords, API keys, and private credentials must not be committed to Git.

The `.env.example` file should contain only safe placeholder values and should be committed to the repository as a configuration reference.


# 17. Testing

AutoInspect includes automated API tests using `pytest` and FastAPI's `TestClient`.

The tests use an isolated in-memory SQLite database and mock the background queue so that API behavior can be tested without requiring PostgreSQL, Redis, or an active RQ worker.

## Automated Test Coverage

The test suite covers:

- Valid JPEG image upload
- Valid PNG image upload
- Valid WebP image upload
- Unique processing ID generation
- Processing status retrieval after upload
- Uploaded image metadata persistence
- Unsupported file type validation
- Invalid image content validation
- Missing image field validation
- Unknown processing ID handling

## Running the Tests

From the project root:

```bash
pytest -v
```


# 18. AI Usage Disclosure

AI tools were used during development as engineering assistants.

## Where AI Was Used

AI assistance was used for:

- Discussing architecture options
- Debugging implementation issues
- Reviewing API behavior
- Designing frontend interaction patterns
- Explaining errors and logs
- Suggesting implementation approaches
- Reviewing edge cases
- Improving documentation
- Helping reason about trade-offs

AI was used as an assistant rather than as an unquestioned source of implementation.


## What AI Helped With

AI assistance was particularly useful for:

- Reasoning about asynchronous image processing
- Understanding Redis/RQ worker behavior
- Debugging frontend-to-backend communication
- Identifying CORS issues
- Designing processing-state handling
- Reviewing error handling
- Structuring the frontend processing timeline
- Thinking through duplicate-detection behavior
- Reviewing API and architecture documentation


## Where AI Output Was Wrong

AI-generated suggestions were not always correct.

Examples encountered during development included:

- Incorrect assumptions about the location of frontend components
- Suggestions that did not match the current project structure
- Incorrect assumptions about frontend/backend processing stages
- Suggestions that required adjustment to match the actual API behavior
- OCR-related expectations that did not always match real image results

For example, the backend exposes overall states such as:

```text
pending
processing
completed
failed
```

rather than individual API states for every visual pipeline stage.

Therefore, the frontend pipeline visualization was treated as a UI representation rather than falsely claiming that the backend provides real-time stage telemetry.


## How AI-Generated Code Was Validated

AI-generated code was validated through:

1. Running the application locally.
2. Testing API endpoints through Swagger.
3. Testing image uploads with valid and invalid files.
4. Checking FastAPI logs.
5. Checking RQ worker logs.
6. Checking PostgreSQL persistence.
7. Testing frontend behavior in the browser.
8. Testing duplicate detection using repeated images.
9. Testing different images.
10. Testing failure and recovery behavior.
11. Testing responsive layouts.

Code was accepted only after its behavior matched the actual system requirements and observed runtime behavior.


# 19. Engineering Trade-offs

## Intentional Simplifications

The project intentionally avoids several production-level complexities to keep the implementation focused.

### Local Image Storage

Images are currently stored locally instead of using cloud object storage.

This keeps the development environment simple and appropriate for a take-home assignment.

### Polling

The frontend uses HTTP polling to retrieve processing status instead of WebSockets or Server-Sent Events.

This is sufficient for the current scale and keeps the architecture straightforward.

### CPU Processing

The current development environment can perform image processing on CPU.

GPU acceleration was not required for demonstrating the architecture.

### Limited Processing States

The backend exposes overall processing states rather than individual states for every analysis component.

The frontend provides a visual five-stage representation of the conceptual analysis pipeline.

````markdown
# 20. Improvements With More Time

With additional development time, the following improvements would be considered:

- More accurate license-plate detection
- Improved OCR preprocessing
- Better Indian number plate format validation
- More robust screenshot/photo-of-photo detection
- Image tampering detection
- GPU acceleration
- Object storage instead of local storage
- WebSocket/SSE-based processing updates
- Authentication and authorization
- Analysis history
- Batch processing
- Automated integration tests
- Improved retry policies
- Monitoring and observability
- Production deployment
- Rate limiting
- API authentication
- Horizontal worker scaling

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

Potential production failure cases include:

- Worker crashes
- Redis unavailability
- Database unavailability
- Corrupted image files
- OCR failure
- Model inference failure
- Large image uploads
- Queue backlog
- Duplicate jobs
- Partial processing

The current implementation handles important application-level failures and exposes a `failed` processing state with an associated failure reason.

Further production improvements could include:

- Automatic job retries
- Retry backoff
- Dead-letter queues
- Worker health monitoring
- Idempotent processing
- Structured logging
- Alerting
- Distributed tracing

# 23. Assumptions

The following assumptions were made during implementation:

1. Vehicle images are uploaded through the API as multipart form data.
2. Only JPEG, PNG, and WebP images are supported.
3. Uploaded images can initially be stored locally.
4. Image processing may take several seconds and therefore must not block the upload request.
5. OCR output is probabilistic and therefore must include confidence information.
6. A matching SHA-256 hash indicates an exact duplicate file.
7. Perceptual similarity is useful for identifying visually similar images even when their file contents differ.
8. The current system is intended as a take-home engineering demonstration rather than a production-scale deployment.
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

Additional production-grade capabilities such as rate limiting, authentication, advanced observability, and production deployment remain future improvements.

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

The frontend intentionally uses a restrained visual design rather than relying on excessive colors or decorative effects.

The processing pipeline is presented visually to communicate the underlying architecture without pretending that the backend exposes telemetry that it does not actually provide.

# 26. Limitations

The system should not be considered a production-grade vehicle-inspection or legal number-plate verification system.

OCR accuracy depends on the quality and characteristics of the input image.

Possible limitations include:

- Incorrect OCR
- Missed plate detection
- False duplicate matches
- False negative duplicate detection
- Sensitivity to image quality
- CPU processing time
- Limited tampering detection
- Limited vehicle-specific validation

The analysis results should therefore be interpreted as automated inspection signals rather than absolute ground truth.

# 27. Conclusion

AutoInspect demonstrates an asynchronous image-processing architecture that combines REST APIs, background jobs, persistent storage, image analysis, OCR, duplicate detection, confidence scoring, and explainable results.

The implementation focuses on engineering judgment and reliability rather than attempting to solve every computer-vision problem perfectly.

The architecture can be extended toward a production system by introducing scalable object storage, multiple workers, stronger computer-vision models, automated testing, observability, retries, authentication, and real-time processing updates.