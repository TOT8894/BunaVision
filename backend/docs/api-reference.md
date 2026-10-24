# API reference

## Contents

- [Base behavior](#base-behavior)
- [Error responses](#error-responses)
- [Authentication](#authentication)
- [Assessments](#assessments)
- [Administrator endpoints](#administrator-endpoints)
- [Health and OpenAPI](#health-and-openapi)

This reference is derived from `app/api/routers/`, `app/schemas/`, `app/api/error_status.py`, and the central exception handlers. FastAPI's interactive docs and generated schema are available at runtime as described in [Health and OpenAPI](#health-and-openapi).

## Base behavior

- API routes use the `/api/v1` prefix except `GET /health`.
- JSON request bodies use `Content-Type: application/json`. Assessment uploads use `multipart/form-data` with the exact file field name `image`.
- Protected routes require `Authorization: Bearer <access_token>`. Admin paths require the authenticated user's database role to be `admin`.
- `X-Request-ID` is accepted only when it contains 1–64 ASCII letters, digits, periods, underscores, or hyphens. Otherwise the backend generates a UUID hex ID. Every response from the request middleware includes `X-Request-ID`.
- Error responses use one `error` object. Validation messages include at most five Pydantic issues.

### Shared contract alignment

This reference follows the current backend routers, schemas, and error mapper. During inspection, the checked-in [`contracts/backend-api/openapi.json`](../../contracts/backend-api/openapi.json) and its README were found to differ from that implementation: the contract advertises a 409 response for a changed-image idempotency key (the code returns 422), includes an `Idempotency-Key` character regex that is not enforced by the router (the code enforces only 1–128 characters), and the contract README says uploads may be 15 MB while the backend default is 10 MiB. The committed assessment example also predates required `result.image_check` fields. Treat these as contract drift, not as implemented behavior. A follow-up contract-owner change should regenerate/update the shared OpenAPI and examples from the current code (or make a separately reviewed API change), then obtain frontend/backend review. This documentation task does not edit files outside `backend/`.

## Error responses

Example (null fields are included by the current response model):

```json
{
  "error": {
    "code": "INVALID_IMAGE",
    "message": "The uploaded file is not a readable image.",
    "request_id": "9b1f0c5e7a2d4e6f8a3b1c2d4e5f6a7b",
    "assessment_id": null,
    "details": null
  }
}
```

`message` is the public-safe message. `assessment_id` is set when the accepted workflow created an ID; `details` is used for safe machine-readable facts such as the coffee-gate confidence. Authentication failures include `WWW-Authenticate: Bearer`. Rate limiting includes `Retry-After` in seconds.

| HTTP | Error codes |
|---:|---|
| 400 | `INVALID_IMAGE` |
| 401 | `AUTHENTICATION_REQUIRED`, `INVALID_CREDENTIALS` |
| 403 | `FORBIDDEN` |
| 404 | `ASSESSMENT_NOT_FOUND` |
| 409 | `EMAIL_ALREADY_REGISTERED` |
| 413 | `IMAGE_TOO_LARGE` |
| 415 | `UNSUPPORTED_FORMAT` |
| 422 | `IMAGE_NOT_COFFEE`, `INVALID_REQUEST`, `IDEMPOTENCY_KEY_REUSED` |
| 429 | `RATE_LIMITED` |
| 500 | `INTERNAL_ERROR` |
| 502 | `INFERENCE_FAILED`, `ADVISORY_FAILED`, `MODEL_RELOAD_FAILED` |
| 503 | `PERSISTENCE_FAILED` |
| 504 | `INFERENCE_TIMEOUT` |

Not every code applies to every endpoint. FastAPI request validation is converted to `422 INVALID_REQUEST`; unmatched HTTP exceptions use `INVALID_REQUEST` with the exception's status. Unhandled exceptions become `500 INTERNAL_ERROR`.

## Authentication

### `POST /api/v1/auth/register`

Create a regular user. Authentication: none. Request: JSON `RegisterIn`, exact fields `email` (string, maximum 254 characters) and `password` (10–128 characters); extra fields are rejected. The service trims/lowercases email and applies a conservative email-shape check. Success: `201` with `UserOut`. Errors: `409 EMAIL_ALREADY_REGISTERED`, `422 INVALID_REQUEST`.

```sh
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"producer@example.com","password":"example-only-password"}'
```

```json
{"user_id":"<uuid>","email":"producer@example.com","role":"user","created_at":"2026-10-24T12:00:00Z"}
```

### `POST /api/v1/auth/login`

Exchange email and password for a bearer access token. Authentication: none. Request: JSON fields `email` (maximum 254 characters) and `password` (maximum 128 characters); extra fields are rejected. Success: `200` with `TokenOut`. Errors: `401 INVALID_CREDENTIALS`, `422 INVALID_REQUEST`. Unknown email and incorrect password share the same public error.

```sh
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"producer@example.com","password":"example-only-password"}'
```

```json
{"access_token":"<jwt>","token_type":"bearer","expires_in_s":3600}
```

### `GET /api/v1/auth/me`

Return the active signed-in user. Authentication: bearer token. No query, path, or body parameters. Success: `200 UserOut` with `user_id`, `email`, `role`, and `created_at`. Error: `401 AUTHENTICATION_REQUIRED`.

```sh
curl http://localhost:8000/api/v1/auth/me -H 'Authorization: Bearer <jwt>'
```

```json
{"user_id":"<uuid>","email":"producer@example.com","role":"user","created_at":"2026-10-24T12:00:00Z"}
```

There is no HTTP endpoint to list, deactivate, promote, or delete users. See [security](security.md#authorization).

## Assessments

### `POST /api/v1/assessments`

Run a preliminary assessment. Authentication: bearer token; the assessment is owned by that user. Request: `multipart/form-data` with file field `image`. The API checks decoded JPEG, PNG, or WEBP content, the configured byte limit (default 10 MiB), pixel limit (default 50,000,000), and minimum side length (default 320 px). It does not trust the filename or MIME header. The total request-body ceiling is `MAX_IMAGE_BYTES + 65536` bytes.

Optional header: `Idempotency-Key`, 1–128 characters. Use the same key only when retrying the same image bytes for the same user. A new result returns `201 CompletedAssessmentOut`; replay of a prior completed result returns `200` with the same response shape.

Errors: `400 INVALID_IMAGE`, `401 AUTHENTICATION_REQUIRED`, `413 IMAGE_TOO_LARGE`, `415 UNSUPPORTED_FORMAT`, `422 IMAGE_NOT_COFFEE` / `INVALID_REQUEST` / `IDEMPOTENCY_KEY_REUSED`, `429 RATE_LIMITED`, `502 INFERENCE_FAILED` / `ADVISORY_FAILED`, `503 PERSISTENCE_FAILED`, `504 INFERENCE_TIMEOUT`. Busy/quota responses include `Retry-After`. A non-coffee rejection includes `details.is_coffee=false`, `coffee_confidence`, and `threshold` when Vision supplied it. Invalid image and non-coffee rejection do not create assessment records.

```sh
curl -X POST http://localhost:8000/api/v1/assessments \
  -H 'Authorization: Bearer <jwt>' \
  -H 'Idempotency-Key: upload-2026-10-24-001' \
  -F 'image=@sample.jpg;type=image/jpeg'
```

`CompletedAssessmentOut` has `assessment_id`, literal status `completed`, `created_at`, `processing_time_ms`, and `result`. `result` contains `model_version`, `image_check` (`is_coffee: true`, `coffee_confidence`, `validator_version`), `summary` (`detection_count`, primary/secondary detection counts, and `by_class`), `detections` (`defect`, confidence, pixel `box`), `coverage` (`scanned`, `not_scanned`), `limitations`, bilingual `advisory`, and `images` (`original_url`, `annotated_url`, `expires_in_s`). Confidence is model confidence, not correctness; counts are defect detections, not beans. `images` URLs may be null and S3 URLs expire.

Example response shape (illustrative values, not a model result):

```json
{
  "assessment_id": "asmt_<uuid-hex>",
  "status": "completed",
  "created_at": "2026-10-24T12:00:00Z",
  "processing_time_ms": 2140,
  "result": {
    "model_version": "<vision-model-version>",
    "image_check": {"is_coffee": true, "coffee_confidence": 0.97, "validator_version": "<validator-version>"},
    "summary": {"detection_count": 0, "primary_detection_count": 0, "secondary_detection_count": 0, "by_class": []},
    "detections": [],
    "coverage": {
      "scanned": [
        {"key": "full_black", "name": "Full Black", "category": "primary"},
        {"key": "partial_black", "name": "Partial Black", "category": "secondary"},
        {"key": "parchment_husk", "name": "Coffee Husk / Parchment", "category": "secondary"}
      ],
      "not_scanned": [
        {"key": "full_sour", "name": "Full Sour / Stinker", "category": "primary"},
        {"key": "pod", "name": "Pod", "category": "primary"},
        {"key": "fungus_mold", "name": "Fungus / Mold", "category": "primary"},
        {"key": "severe_insect_damage", "name": "Severe Insect Damage", "category": "primary"},
        {"key": "foreign_matter", "name": "Foreign Matter", "category": "primary"},
        {"key": "partial_sour", "name": "Partial Sour", "category": "secondary"},
        {"key": "floater", "name": "Floater / Chalky", "category": "secondary"},
        {"key": "immature", "name": "Immature / Quaker", "category": "secondary"},
        {"key": "broken_chipped", "name": "Broken / Chipped", "category": "secondary"},
        {"key": "slight_insect_damage", "name": "Slight Insect Damage", "category": "secondary"}
      ]
    },
    "limitations": [
      {"code": "PRELIMINARY_AI_ASSESSMENT", "message": "Preliminary AI screening of a photograph. This is not an official ECX or SCA grade."},
      {"code": "PARTIAL_CLASS_COVERAGE", "message": "Only 3 of 13 ECX defect classes are scanned (Full Black, Partial Black, Coffee Husk / Parchment). Defects in the other 10 classes are not detected, so real defect counts may be higher."},
      {"code": "HIDDEN_DEFECTS_NOT_DETECTABLE", "message": "Defects hidden from the camera, or inside the bean, cannot be detected from a photograph."},
      {"code": "MANUAL_VERIFICATION_REQUIRED", "message": "Counts are model predictions. Verify them manually before any commercial or export decision."}
    ],
    "advisory": {"generator_model": "<gemini-model>", "summary": {"en": "<English>", "am": "<Amharic>"}, "recommendations": [{"en": "<English>", "am": "<Amharic>"}]},
    "images": {"original_url": null, "annotated_url": null, "expires_in_s": 900}
  }
}
```

The response values above are illustrative, not a model output. Zero detections is a valid result.

### `GET /api/v1/assessments`

List only the caller's assessments, newest first. Authentication: bearer token. Query: `limit` integer 1–100, default 20; `cursor` opaque string, maximum 512 characters, from the prior page's `next_cursor`. Success: `200 AssessmentListOut`, with `items` and nullable `next_cursor`. Items are discriminated by `status`: completed items include version and detection counts; failed items include `error_code`. Errors: `401 AUTHENTICATION_REQUIRED`, `422 INVALID_REQUEST` for invalid parameters/cursor.

```sh
curl 'http://localhost:8000/api/v1/assessments?limit=20' \
  -H 'Authorization: Bearer <jwt>'
```

```json
{"items":[],"next_cursor":null}
```

### `GET /api/v1/assessments/{assessment_id}`

Fetch one caller-owned assessment, with fresh image URLs where stored. Authentication: bearer token. Path `assessment_id`: string length 1–64. No body or query parameters. Success: `200 AssessmentOut`, either the completed response shape above or a failed object with `assessment_id`, literal status `failed`, `created_at`, `processing_time_ms`, and `error_code`. Errors: `401 AUTHENTICATION_REQUIRED`, `404 ASSESSMENT_NOT_FOUND` (used for both a missing ID and another owner's ID), `422 INVALID_REQUEST` for path validation.

```sh
curl 'http://localhost:8000/api/v1/assessments/asmt_<uuid-hex>' \
  -H 'Authorization: Bearer <jwt>'
```

```json
{"assessment_id":"asmt_<uuid-hex>","status":"failed","created_at":"2026-10-24T12:00:00Z","processing_time_ms":1840,"error_code":"INFERENCE_TIMEOUT"}
```

## Administrator endpoints

All `/api/v1/admin` routes require a bearer token and database role `admin`. Missing/invalid auth returns 401; a regular user receives `403 FORBIDDEN`. There are no request bodies except where explicitly noted below.

### `GET /api/v1/admin/assessments`

List assessments across all owners, newest first. Optional query filters: `status` (`completed` or `failed`), `error_code` (an `ErrorCode` value), `owner_id` (UUID), `limit` integer 1–100 default 20, and opaque `cursor` maximum length 512. Success: `200 AdminAssessmentListOut` containing `items` and nullable `next_cursor`. Each item has `assessment_id`, `owner_id`, `status`, `created_at`, `processing_time_ms`, nullable `error_code`, nullable `model_version`, nullable `validator_version`, and nullable `detection_count`. Error: `422 INVALID_REQUEST` for invalid filters/cursor.

```sh
curl 'http://localhost:8000/api/v1/admin/assessments?status=failed&limit=20' \
  -H 'Authorization: Bearer <admin-jwt>'
```

```json
{"items":[],"next_cursor":null}
```

### `GET /api/v1/admin/assessments/{assessment_id}`

Fetch one assessment regardless of owner. Path `assessment_id`: string length 1–64. Success: `200 AdminAssessmentOut` with the fields listed above. Errors: `404 ASSESSMENT_NOT_FOUND`, `422 INVALID_REQUEST` for path validation.

```sh
curl 'http://localhost:8000/api/v1/admin/assessments/asmt_<uuid-hex>' \
  -H 'Authorization: Bearer <admin-jwt>'
```

```json
{"assessment_id":"asmt_<uuid-hex>","owner_id":"<uuid>","status":"failed","created_at":"2026-10-24T12:00:00Z","processing_time_ms":1840,"error_code":"INFERENCE_TIMEOUT","model_version":null,"validator_version":null,"detection_count":null}
```

### `GET /api/v1/admin/model-versions`

Report completed-assessment usage grouped by Vision `model_version` and coffee `validator_version`. No parameters. Success: `200 {"versions": [...]}`; each item contains `model_version`, `validator_version`, `assessments`, `first_seen`, and `last_seen`. An empty database yields `{"versions":[]}`.

```sh
curl http://localhost:8000/api/v1/admin/model-versions \
  -H 'Authorization: Bearer <admin-jwt>'
```

```json
{"versions":[{"model_version":"<vision-model-version>","validator_version":"<validator-version>","assessments":12,"first_seen":"2026-10-20T08:00:00Z","last_seen":"2026-10-24T11:00:00Z"}]}
```

### `GET /api/v1/admin/overview`

Count persisted outcomes grouped by status/error code since the requested time. Query: `window_hours` integer 1–720, default 24. Success: `200 OverviewOut` with `since`, `window_hours`, and `outcomes` entries (`status`, nullable `error_code`, `count`). Error: `422 INVALID_REQUEST` for invalid window values.

```sh
curl 'http://localhost:8000/api/v1/admin/overview?window_hours=24' \
  -H 'Authorization: Bearer <admin-jwt>'
```

```json
{"since":"2026-10-23T12:00:00Z","window_hours":24,"outcomes":[]}
```

### `GET /api/v1/admin/limits`

Return configured operational limits. No parameters. Success: `200 LimitsOut` with `max_image_bytes`, `max_image_pixels`, `min_image_side_px`, `max_assessments_per_user_per_hour`, `max_concurrent_assessments`, `vision_timeout_s`, `gemini_timeout_s`, `image_url_ttl_s`, and `retain_original_image`. These values describe configuration, not measured capacity.

```sh
curl http://localhost:8000/api/v1/admin/limits \
  -H 'Authorization: Bearer <admin-jwt>'
```

```json
{"max_image_bytes":10485760,"max_image_pixels":50000000,"min_image_side_px":320,"max_assessments_per_user_per_hour":30,"max_concurrent_assessments":4,"vision_timeout_s":30.0,"gemini_timeout_s":30.0,"image_url_ttl_s":900,"retain_original_image":true}
```

### `POST /api/v1/admin/vision/reload-model`

Ask the Vision service to reload its model. Authentication: admin bearer token. No request body or query parameters. Success: `200 {"reloaded": true, "engine": "<engine>"}` using the Vision service response. Error: `502 MODEL_RELOAD_FAILED`. Reloading can time out after `VISION_RELOAD_TIMEOUT_S`; the Vision service may still finish, so inspect its state before retrying. This route is admin-authenticated at the backend; reachability/security of the independently deployed Vision endpoint is an infrastructure concern.

```sh
curl -X POST http://localhost:8000/api/v1/admin/vision/reload-model \
  -H 'Authorization: Bearer <admin-jwt>'
```

```json
{"reloaded":true,"engine":"onnx"}
```

## Health and OpenAPI

### `GET /health`

Unauthenticated liveness endpoint. No path/query/body parameters. Returns `200 {"status":"ok","version":"0.4.0"}` (the version comes from `app.__version__`). It does not check PostgreSQL, Vision, Gemini, or S3.

```sh
curl http://localhost:8000/health
```

FastAPI's built-in Swagger UI, ReDoc, and OpenAPI JSON are available at `/docs`, `/redoc`, and `/openapi.json`. `python -m scripts.export_openapi` writes the generated document to the repository-level `contracts/backend-api/openapi.json`; that command writes outside `backend/`, so it is not part of this backend-only documentation workflow. Do not use it from a task restricted to backend writes.
