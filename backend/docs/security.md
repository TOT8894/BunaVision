# Security controls and gaps

## Contents

- [Authentication](#authentication)
- [Authorization](#authorization)
- [Input and upload validation](#input-and-upload-validation)
- [Quotas and idempotency](#quotas-and-idempotency)
- [Secrets, storage and URLs](#secrets-storage-and-urls)
- [Errors, logging and browser access](#errors-logging-and-browser-access)
- [Known gaps](#known-gaps)

## Authentication

`AuthService` uses `ScryptPasswordHasher` and `JwtTokenIssuer` adapters. Passwords are UTF-8 encoded as entered and hashed with the standard-library scrypt KDF, a random 16-byte salt, and a 32-byte derived key. The production default cost parameters are `N=2^15`, `r=8`, `p=3`; the parameters are included in each stored hash so older hashes can be verified if the cost changes. Hash/verify work runs with `asyncio.to_thread`.

Access tokens are JWTs signed with HS256. The required claims are issuer `bunavision-backend`, subject user ID, issued-at, and expiry. The token contains no role. Every authenticated request reloads the user from PostgreSQL and rejects missing or inactive accounts, so role/activity changes take effect without waiting for token expiry. Token TTL defaults to one hour, is configurable up to 24 hours, and there is no refresh-token endpoint.

Login returns the same `INVALID_CREDENTIALS` response for unknown email and wrong password; unknown users still incur a dummy password verification. Password input length is 10–128 characters, with no additional complexity rule. Email is trimmed/lowercased and checked by a conservative shape regex, not a full RFC validator. Registration has no email-verification step.

## Authorization

- `/api/v1/auth/me`, assessment creation, listing, and item reads require an active user's bearer token.
- Owner assessment reads include the current user ID in the repository query. A missing assessment and another user's assessment both return `404 ASSESSMENT_NOT_FOUND`.
- Every `/api/v1/admin` route applies `require_admin`, which checks the current database role. A user role receives 403.
- The public registration route always creates a regular `user` role. There is no public role-promotion, account-deactivation, or user-delete API. Admin creation is an operator script requiring database access.

## Input and upload validation

Pydantic schemas forbid extra fields for registration/login and constrain query/path values. The ASGI request-size middleware checks `Content-Length` and counts streamed body bytes, limiting request bodies to `MAX_IMAGE_BYTES + 64 KiB` by default. The upload reader separately caps image bytes. Pillow identifies actual image content and fully decodes it; JPEG, PNG, and WEBP are supported. Pixel count and minimum width/height are checked before full decode. Filenames and client MIME headers are not trusted.

This is application validation only; reverse proxies, load balancers, and the Vision service have their own limits. Keep those limits compatible with the configured image maximum.

## Quotas and idempotency

The hourly quota defaults to 30 persisted attempts per user and includes completed results and recorded dependency failures. It is not a general request rate limiter: it does not throttle login, registration, health, or arbitrary traffic. When limited, the error is 429 and carries `Retry-After`.

The active-assessment cap defaults to four slots in one `AssessmentService` instance. A process-local lock/event serializes a same-owner count/create sequence. These controls are not distributed across workers or containers. The quota check and insert are separate database operations, so multiple processes can race and exceed the hourly limit. This is a known consistency limitation, not a global enforcement guarantee.

An optional `Idempotency-Key` is limited to 1–128 characters and scoped by owner. PostgreSQL's partial unique index protects a completed key from duplicate insert. The workflow compares SHA-256 of the uploaded bytes before replaying; reusing the key with different bytes returns `422 IDEMPOTENCY_KEY_REUSED`. Failed attempts discard the key, allowing retries. A same-key concurrent request waits/replays within one process; the database index handles cross-process duplicate inserts, but there is no distributed admission lock.

## Secrets, storage and URLs

`GEMINI_API_KEY`, `DATABASE_URL`, and `JWT_SECRET` use Pydantic `SecretStr`; `JWT_SECRET` must be at least 32 characters. AWS credentials are obtained through boto3's default credential chain rather than stored in backend settings. Store production values in the deployment platform's secret manager or protected environment, not in source control. See [configuration](configuration.md).

The S3 adapter expects a private bucket and requests only the S3 operations it needs in its code comments (`PutObject`, `GetObject` for presigning, and `DeleteObject`). The backend does not create or verify bucket policy, encryption policy, network controls, or IAM role restrictions. Those are infrastructure responsibilities. S3 URLs are signed for `IMAGE_URL_TTL_S` (default 900 seconds). Anyone who obtains a presigned URL can use it until it expires; the URL is a bearer capability and is not re-authorized by the API on each image download. URLs are generated at response time and not stored in PostgreSQL.

With `RETAIN_ORIGINAL_IMAGE=false`, original image bytes are not stored by the backend after processing, but the image is still sent to Vision. An annotated image is still stored if Vision returns one. Gemini receives only derived summary/coverage facts. `IMAGE_STORE=memory` loses images on restart and does not provide browser-fetchable URLs.

## Errors, logging and browser access

The common API error envelope returns public messages and a request ID rather than raw Python tracebacks. Unhandled exceptions are written to logs with traceback; intentional dependency failures are also logged with exception details. Request logs include a `request_id` context field. The logging code does not implement a general-purpose secret/personal-data redaction filter, so protect logs and avoid putting secrets or personal information in error details. Passwords and bearer tokens are not explicitly logged by the authentication path.

CORS is disabled when `CORS_ALLOWED_ORIGINS` is empty (the default). When configured, `*` is rejected, methods are limited to GET/POST, allowed headers are Authorization, Content-Type, Idempotency-Key and X-Request-ID, credentials are disabled, and X-Request-ID is exposed. CORS is a browser policy, not network access control. `GET /health` only returns liveness and version, not configuration or dependency status.

## Known gaps

- There is no login brute-force/IP/email throttling and no registration rate limiter.
- Quota and concurrency protections are process-local or non-atomic across processes, as described above.
- `VISION_SERVICE_URL` accepts HTTP as well as HTTPS. The application does not enforce TLS or private networking; configure secure service-to-service networking at deployment.
- The backend reload route is admin-authenticated, but the backend does not establish that the independently hosted Vision `/reload-model` endpoint itself is authenticated or network-restricted. The checked-in Vision service route has no auth dependency; protect its network path at infrastructure level before exposing it.
- The S3 adapter documents a private bucket requirement, but bucket/IAM policies are not provisioned or checked by this repository.
- Presigned image URLs can be shared and used until expiry. There is no per-fetch ownership check after a URL is issued.
- The current backend consumer's required coffee-validator response fields do not match the checked-in Vision source/contract; see [Vision integration](vision-integration.md#source-level-contract-mismatch).
