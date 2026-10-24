# Backend architecture

## Contents

- [Runtime structure](#runtime-structure)
- [Assessment request lifecycle](#assessment-request-lifecycle)
- [Dependency and error flow](#dependency-and-error-flow)
- [Admission controls](#admission-controls)
- [Implemented scope and gaps](#implemented-scope-and-gaps)

## Runtime structure

The FastAPI application is built by `app.api.app.create_app` and exposed through `app.main:create_app`. The app factory creates settings and registers routers, middleware, and centralized error handlers. During its lifespan, `app.container.build_services` opens the PostgreSQL engine, verifies the schema, creates the Vision HTTP and Gemini clients, wires the service bundle, and closes these resources during shutdown.

The code keeps transport, workflow, domain, and integration details in separate layers:

| Layer | Location | Responsibility |
|---|---|---|
| HTTP | `app/api/` | Routers declare paths, request/response models, and service dependencies. Middleware adds request IDs and caps request bodies. Error handlers translate domain and framework failures to the common envelope. |
| Public schemas | `app/schemas/` | Pydantic API input and output contracts; these are separate from database records and domain entities. |
| Services | `app/services/` | `AssessmentService`, `AuthService`, and `AdminService` implement use cases and workflow ordering. Services depend on protocols in `ports.py`, not on HTTPX, boto3, or SQLAlchemy. |
| Domain | `app/domain/` | Frozen domain records, error codes, the defect taxonomy, detection summaries, coverage, and limitations. It has no transport or persistence responsibilities. |
| Adapters | `app/adapters/` | PostgreSQL repositories, Vision HTTP client, Gemini advisor, S3/memory image stores, scrypt password hasher, and JWT issuer. |
| Composition/configuration | `app/container.py`, `app/core/` | Selects concrete adapters, loads typed environment settings, and provides clock/ID/logging utilities. |

Dependencies flow inward from the API to services and domain rules. Adapters implement service ports; the composition root wires them. The HTTP routes do not access database or cloud SDKs directly. PostgreSQL is the production repository implementation. In-memory repositories exist for tests and local service construction but are not selected by the production container.

## Assessment request lifecycle

```mermaid
sequenceDiagram
    actor Client
    participant ASGI as Middleware and FastAPI router
    participant Auth as AuthService
    participant Workflow as AssessmentService
    participant DB as PostgreSQL repository
    participant Vision as Vision HTTP service
    participant Gemini as Gemini advisor
    participant Store as ImageStore (memory or S3)

    Client->>ASGI: POST /api/v1/assessments (multipart image, bearer token)
    ASGI->>Auth: Resolve current user from token and database
    Auth-->>ASGI: Active user
    ASGI->>Workflow: create_assessment(bytes, owner, optional key)
    Workflow->>DB: Look up existing owner/key (if supplied)
    Workflow->>DB: Count owner's persisted attempts in last hour
    Workflow->>Workflow: Enforce in-process admission; decode and validate image in worker thread
    Workflow->>Vision: POST /detect with image bytes
    Vision-->>Workflow: Validator/model versions and detections (or explicit error)
    Workflow->>Workflow: Map labels, summarize detections and derive coverage
    Workflow->>Gemini: Derived summary and coverage only
    Gemini-->>Workflow: Schema-validated bilingual advisory
    Workflow->>Store: Save retained original and optional annotated JPEG
    Workflow->>Store: Create response-time image URLs
    Workflow->>DB: Insert completed result
    DB-->>Workflow: Commit
    Workflow-->>ASGI: Completed assessment view
    ASGI-->>Client: 201 created, or 200 for an idempotent replay
```

The router enforces multipart handling and reads no more than the configured image ceiling plus one byte. Request-size middleware limits the whole request body to the image ceiling plus 64 KiB for multipart framing. `AssessmentService` checks idempotency and quota, takes an instance-local owner guard and concurrency slot, then calls image validation via `asyncio.to_thread`. It calls Vision, maps each `class_name` through `ECX_TAXONOMY`, computes detection counts and coverage, and calls Gemini with those facts. It stores image objects after detection and advisory succeed, signs URLs, then inserts the completed assessment.

The response mapper (`app/api/mappers.py`) recomputes the public shape from domain data. Summary values are recomputed from detections when stored JSONB is rehydrated; they are not an independently stored count source. Every completed result carries the Vision `model_version` and coffee-validator `validator_version`.

## Dependency and error flow

Authentication dependencies validate the bearer JWT, then reload the user row so account activity and role are current. The route passes the user ID to services; owner-scoped repository queries include that ID. Admin routes add `require_admin` before invoking `AdminService`.

Domain errors do not contain HTTP status logic. `app.api.error_status` maps domain error codes to status codes, and `app.api.error_handlers` returns:

```json
{
  "error": {
    "code": "INFERENCE_FAILED",
    "message": "The image analysis service is unavailable. Please try again.",
    "request_id": "<request-id>",
    "assessment_id": "<id-or-null>",
    "details": null
  }
}
```

Validation failures are `INVALID_REQUEST` errors; unexpected exceptions are logged and returned as `INTERNAL_ERROR`. `X-Request-ID` is echoed on responses; a syntactically acceptable incoming ID is reused, otherwise a UUID hex ID is generated. Rate-limit errors also include `Retry-After` in seconds. See the [API reference](api-reference.md#error-responses) for the complete status map.

Bad input, including a malformed image, and the Vision coffee-gate rejection are caller errors and do not create assessment rows. A downstream dependency failure after the workflow has allocated an assessment ID is re-raised and, for `DependencyError` subclasses, the service tries to save a failed row with its error code. If that failure record cannot be written, the service logs the secondary failure and returns the original error. If image storage, URL signing, or final persistence fails, image cleanup is attempted; cleanup is best-effort and a cleanup failure is logged.

## Admission controls

- **Hourly quota:** the service counts persisted completed and failed attempts for an owner over the preceding hour. Invalid images and photos rejected by the coffee gate do not create persisted attempts. A replay of an earlier successful idempotency key is checked before quota enforcement and does not consume another slot.
- **Concurrent assessments:** an `asyncio.Semaphore` rejects a request when all configured service-instance slots are busy instead of queuing it.
- **Same-owner admission:** a process-local lock/event serializes the count-and-create path for a given owner. For no-key concurrent requests, the later request receives 429. A concurrent request using the same key waits and then replays the stored result if the first request succeeded.
- **Database idempotency:** a PostgreSQL partial unique index on `(owner_id, idempotency_key)` protects a completed result from duplicate keys. The key is omitted from failed rows, permitting a retry after a downstream failure.
- **Pagination:** repositories use descending keyset pagination over `(created_at, assessment_id)`, not offset pagination.

The semaphore and owner lock live in one `AssessmentService` instance. They do not coordinate multiple worker processes or containers. The database uniqueness index protects key uniqueness across processes, but hourly quota counting is not a global atomic reservation. See [security](security.md#quotas-and-idempotency) and [database](database.md#constraints-and-indexes).

## Implemented scope and gaps

Implemented: registration/login/current-user, owner-scoped assessment creation and history, admin read-only assessment diagnostics, model-version/outcome/limit views, and admin-triggered Vision model reload.

Not implemented: a public user-management/deactivation API, refresh tokens, login brute-force throttling, official grading, bean totals, image preprocessing, queue-based inference, global/distributed quota locks, or a production Vision deployment. No adapter calls a model locally. The [deployment](deployment.md) page separates the checked-in Docker/Compose setup from infrastructure not defined in this repository.
