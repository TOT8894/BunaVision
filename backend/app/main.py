"""Process entry point: `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000`."""

from app.api.app import create_app

__all__ = ["create_app"]
