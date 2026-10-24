# Vision service integration

## Contents

- [Backend client contract](#backend-client-contract)
- [Image checks before Vision](#image-checks-before-vision)
- [Response mapping](#response-mapping)
- [Failures and cleanup](#failures-and-cleanup)
- [Source-level contract mismatch](#source-level-contract-mismatch)
- [Local development](#local-development)

## Backend client contract

The only backend access path is `app.adapters.vision_client.HttpVisionDetector` and `HttpVisionAdmin`; the backend does not import the Vision service's Python modules. The base URL is `VISION_SERVICE_URL` and the backend creates one shared `httpx.AsyncClient` with `VISION_TIMEOUT_S` (default 30 seconds) and `VISION_CONNECT_TIMEOUT_S` (default 3 seconds) for inference.

### `POST /detect`

The backend sends `multipart/form-data` with field name `file`, a neutral filename such as `upload.jpg`, the decoded-content MIME type, and the original validated image bytes. It forwards the request's `X-Request-ID`. It does not send a `confidence` query parameter; any Vision-side query default therefore applies.

The response must be HTTP 200 and parse as JSON with these fields:

| Field | Backend validation/use |
|---|---|
| `model_version` | Non-empty string; stored on completed result and assessment row |
| `validator_version` | Non-empty string; stored on completed result and assessment row |
| `is_coffee` | Required boolean; `false` becomes a non-coffee rejection |
| `coffee_confidence` | Required number from 0 through 1; returned in the result's image check |
| `detected_beans` | Required list; each item needs `class_name`, `confidence` 0–1, and `box` with numeric `x1`, `y1`, `x2`, `y2` where `x2 > x1` and `y2 > y1` |
| `annotated_image_base64` | Optional nullable string; if present must be valid base64 whose decoded bytes begin with the JPEG signature |

Unknown response fields are ignored. `category`, summary counters, and class counts from Vision are not trusted or used. The backend derives taxonomy categories and summary counts from mapped detections.

### Coffee-gate rejection shape

The adapter recognizes HTTP 400 JSON shaped as `{"detail":{"code":"IMAGE_NOT_COFFEE","message":"...","confidence":0.02,"threshold":0.5}}`. `message` and optional `threshold` are accepted; `confidence` is required and range-checked. It also treats a 200 response with `is_coffee: false` as the same client rejection. The public backend error is `422 IMAGE_NOT_COFFEE` with `details.is_coffee=false`, `coffee_confidence`, and threshold when available. The request is not recorded as an assessment.

### `POST /reload-model`

The admin adapter sends an empty POST with `X-Request-ID`, using `VISION_RELOAD_TIMEOUT_S` (default 60 seconds). It expects a 200 JSON response with boolean `reloaded` and non-empty `engine`; extra response fields are ignored. The backend exposes this call only through admin-authenticated `POST /api/v1/admin/vision/reload-model`. No backend call is made to the Vision `/health` endpoint.

## Image checks before Vision

Before the HTTP call, the backend reads the upload with a byte ceiling and decodes its actual contents using Pillow. Supported formats are JPEG, PNG, and WEBP. It rejects empty, corrupt/truncated, over-byte-limit, over-pixel-limit, or too-small images. It does not resize, rotate, or re-encode them. The exact size limits are configurable; see [configuration](configuration.md#application-settings).

The client filename and browser MIME type do not determine the Vision filename or type. The outgoing filename and content type are selected from the decoded image format.

## Response mapping

Each Vision `detected_beans` element is treated as one defect detection (one bounding box), despite the Vision field name. `class_name` must exactly match a taxonomy `vision_label`. The current backend taxonomy marks three of thirteen listed classes as scanned: `Full Black`, `Partial Black`, and `Coffee Husk / Parchment`; `Partial Black` maps to secondary, the other two to their domain categories. Unknown labels fail with `INFERENCE_FAILED` and are not guessed.

The backend computes total, primary, and secondary detection counts, per-class tallies, mean confidence, coverage, and the report's limitation messages. Confidence is the detector's model score, not confidence that a finding is correct. It does not calculate bean totals, healthy-bean counts, defect percentages, grades, export eligibility, or cupping scores. Gemini receives the derived counts and coverage only, not image bytes or free-form user text.

If `RETAIN_ORIGINAL_IMAGE=true`, the original is stored after the advisory succeeds. A returned annotated image is stored as `annotated.jpg` whether or not original retention is enabled. If the detector omits the annotation, `annotated_url` is null. If subsequent URL signing or database insertion fails, the service attempts to delete objects it wrote; cleanup is best-effort. `IMAGE_STORE=memory` returns unusable `memory://` URLs; S3 returns time-limited presigned URLs.

## Failures and cleanup

| Vision condition | Backend handling |
|---|---|
| Request timeout | `504 INFERENCE_TIMEOUT`; failed assessment is recorded when possible |
| Transport error, HTTP 5xx, or HTTP 429 | `502 INFERENCE_FAILED`; failed attempt is recorded when possible |
| HTTP 400 with recognized `IMAGE_NOT_COFFEE` body, or 200 `is_coffee=false` | `422 IMAGE_NOT_COFFEE`; no assessment row |
| Other HTTP 400 | `502 INFERENCE_FAILED` as an unusable Vision response |
| Other non-200 status, including any 3xx/4xx not handled above | `502 INFERENCE_FAILED` |
| Missing/invalid required response fields, invalid box order, invalid base64, or non-JPEG annotation | `502 INFERENCE_FAILED`; failed attempt is recorded when possible |
| Vision returns an unknown defect label | Taxonomy mapping fails explicitly; `502 INFERENCE_FAILED` and a failed attempt is recorded when possible |

No retry or mock fallback is implemented in the backend Vision adapter. A dependency failure is not converted to a successful zero-detection result.

## Source-level contract mismatch

There is a verified mismatch between the current backend consumer and the checked-in Vision service source/contract. The backend's `VisionDetectResponse` requires `validator_version`, `is_coffee`, and `coffee_confidence`. The current [`vision/core/schemas.py`](../../vision/core/schemas.py) `YOLODetectionResult` and [`vision/service/main.py`](../../vision/service/main.py) response provide `model_version`, bean/detection counters, `detected_beans`, and optional annotation, but do not provide those three required coffee-check fields. The Vision service's current HTTP 400 error for an empty/invalid upload also uses a string `detail`, while the backend coffee rejection parser requires `detail.code == "IMAGE_NOT_COFFEE"` and confidence.

The checked-in [Vision OpenAPI contract](../../contracts/vision-api/openapi.json) has the same older result shape and does not declare the backend's coffee-gate fields. Consequently, a successful response from the checked-in Vision implementation cannot satisfy the backend's current `VisionDetectResponse` schema, and its current invalid-image HTTP 400 is not recognized as `IMAGE_NOT_COFFEE`. The Vision README also describes Gemini bean-total estimation, while current backend code deliberately exposes no bean totals. The backend-side documentation here describes what the backend client actually requires; it does not silently redefine the shared contract.

This source comparison does not prove what a deployed Vision URL currently returns. No live Vision request was made as part of this documentation work. Proposed follow-up: Backend and Vision owners should agree whether the Vision service will add the coffee-gate/version fields or the backend consumer will change, then update `contracts/vision-api/openapi.json` and both implementations in one reviewed contract change. Do not resolve the mismatch by documentation alone. Backend admin reload is shape-compatible with the current Vision reload response (`reloaded` and `engine`), but it too has not been live-tested here.

## Local development

The backend Compose file does not start Vision. The Vision service source and README describe running it separately on port 9000, and a containerized backend uses `http://host.docker.internal:9000` by default. That hostname must resolve from the backend container on the target Docker platform. A successful backend process startup does not validate Vision connectivity or response compatibility.

For contract-level backend tests, run `python -m pytest tests/adapters/test_vision_client.py`. Those tests use `httpx.MockTransport`; they do not contact the deployed service, load model artifacts, or measure detection quality. See [testing](testing.md#test-groups-and-limits).
