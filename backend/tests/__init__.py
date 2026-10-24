"""Use the same async event loop in tests that Uvicorn auto-selects at runtime."""

try:
    import uvloop
except ImportError:  # pragma: no cover - optional on platforms without uvloop support
    pass
else:
    uvloop.install()
