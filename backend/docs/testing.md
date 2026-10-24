# Testing

## Contents

- [Runtime and dependencies](#runtime-and-dependencies)
- [Commands](#commands)
- [Test groups and limits](#test-groups-and-limits)
- [External services](#external-services)
- [Observed local asyncio runtime issue](#observed-local-asyncio-runtime-issue)

## Runtime and dependencies

Tests use pytest (`requirements-dev.txt`) and standard-library `unittest`, including `IsolatedAsyncioTestCase` for async service tests. The `pyproject.toml` declares Python `>=3.11`; the backend Dockerfile is based on `python:3.12-slim`. The repository does not pin a single developer Python patch version. This metadata is not evidence that every Python build/platform has been exercised.

## Commands

Run from `backend/` after installing `requirements-dev.txt`:

```sh
python -m pytest
```

Useful focused runs:

```sh
python -m pytest tests/unit/test_assessment_service.py
python -m pytest tests/unit/test_assessment_service.py::CoffeeGateTests::test_a_non_coffee_photo_is_rejected_and_not_recorded
python -m pytest tests/adapters/test_vision_client.py
python -m pytest tests/api/test_upload_limits.py
```

Pytest is configured to discover tests under `tests/` and to add the backend root to `pythonpath`. It also discovers the standard-library `unittest.TestCase` and `IsolatedAsyncioTestCase` classes in those files.

The repository includes an explicit runtime probe outside normal pytest discovery. To run its two bounded cases, use an outer process timeout as well as the in-script asyncio deadline:

```sh
timeout 5s python tests/runtime_probe.py to-thread
timeout 5s python tests/runtime_probe.py call-soon-threadsafe
```

The first case awaits `asyncio.to_thread(time.sleep, 0.1)` under `asyncio.wait_for`; the second starts a worker thread that calls `loop.call_soon_threadsafe`. The OS timeout matters because an asyncio timer cannot guarantee process termination if the loop or executor shutdown is stalled.

## Test groups and limits

| Tests | Coverage |
|---|---|
| `tests/unit/test_domain.py`, `test_users.py` | Taxonomy inventory/mapping, zero and nonzero detection summaries, limitations, assessment invariants, email normalization and password input bounds |
| `tests/unit/test_image_validation.py` | Actual Pillow decode, supported formats, empty/corrupt/truncated data, byte/pixel/minimum-side limits |
| `tests/unit/test_assessment_service.py` | Assessment workflow with fake Vision/advisor and in-memory repository/store; coffee rejection, failures, quotas, idempotency, cleanup and owner-scoped reads |
| `tests/unit/test_auth_service.py`, `test_security.py` | Registration/login/authentication behavior, scrypt verification, JWT claims, expiry, signatures and roles/account state refreshed from repository |
| `tests/unit/test_admin_service.py` | Admin query behavior, outcome/version counts, limits and fake reload port |
| `tests/unit/test_repository.py` | In-memory repository behavior and opaque cursor encode/decode; it does not exercise PostgreSQL SQL |
| `tests/unit/test_serialization.py` | JSON result serialization, schema version, recomputed summary and invalid stored values |
| `tests/unit/test_config.py`, `test_error_status.py` | Selected settings validation and complete error-code/status mapping, including Retry-After |
| `tests/adapters/test_vision_client.py` | HTTPX `MockTransport` response parsing, contract rejection and timeout/error mapping |
| `tests/api/test_upload_limits.py` | Request-size middleware with a direct ASGI transport, including streamed/chunked body rejection |

These are unit tests and mocked adapter/middleware tests. The repository does not configure a PostgreSQL integration-test fixture, a live HTTP integration test against Vision or Gemini, a real S3/MinIO test, or a test of deployed model artifacts. Passing these tests would not establish production availability, model accuracy, or backend/Vision contract compatibility.

## External services

The test groups listed above are designed to run without live PostgreSQL, Vision, Gemini, AWS credentials, or an S3 bucket. They use fakes, an in-memory repository/store, or HTTPX mock transport. The backend application itself does require valid settings and a reachable, migrated PostgreSQL database during lifespan startup; that is separate from these unit tests. No app-level end-to-end test harness is configured in this directory.

## Observed local asyncio runtime issue

In a standalone probe on the current development environment, CPython 3.13.12 and 3.14.8 (Linux x86_64, `_UnixSelectorEventLoop`, `_UnixDefaultEventLoopPolicy`) both timed out while awaiting `asyncio.to_thread(time.sleep, 0.1)` with a two-second `asyncio.wait_for`. The probe process then required the outer five-second `timeout` to terminate (exit status 124). The separately run `call_soon_threadsafe` case passed on both versions. The existing 3.14.8 virtual environment showed the same result as the isolated system interpreter.

This is a point-in-time observation, not a confirmed selector/epoll root cause and not a test-suite result. Python 3.12 was not available for that comparison. No assessment-service or full application suite result was produced from that runtime investigation. If the probe stalls locally, compare a clean Python 3.12 environment (the container base), a stock CPython build, and another host before drawing a root-cause conclusion; do not treat the probe timeout as an application pass or alter production asyncio behavior to mask it. See [troubleshooting](troubleshooting.md#asyncio-to_thread-probe-times-out).
