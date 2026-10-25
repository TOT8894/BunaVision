"""Write the backend's OpenAPI document to contracts/backend-api/openapi.json.

    python -m scripts.export_openapi

The frontend generates its TypeScript types from that file. Placeholder settings are used
because building the schema opens no connections. CI should run this and fail if the committed
file differs from the generated one.
"""

import json
from pathlib import Path

from app.api.app import create_app
from app.core.config import ImageStoreBackend, Settings

OUTPUT = Path(__file__).resolve().parents[2] / "contracts" / "backend-api" / "openapi.json"


def main() -> None:
    settings = Settings(
        _env_file=None,
        vision_service_url="http://localhost:9000",
        gemini_api_key="placeholder",
        gemini_model="placeholder",
        image_store=ImageStoreBackend.MEMORY,
        database_url="postgresql+asyncpg://placeholder:placeholder@localhost/placeholder",
        jwt_secret="p" * 32,
    )  # type: ignore[call-arg]
    schema = create_app(settings).openapi()
    OUTPUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
