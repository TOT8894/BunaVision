"""Write the backend OpenAPI document to contracts/backend-api/openapi.json.

Uses throwaway settings and never starts the app, so it needs no real credentials or services:

    python -m scripts.export_openapi
"""

import json
from pathlib import Path

from app.core.config import AssessmentStoreBackend, ImageStoreBackend, Settings
from app.main import create_app

OUTPUT = Path(__file__).resolve().parents[2] / "contracts" / "backend-api" / "openapi.json"


def main() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        vision_service_url="http://vision.invalid",  # type: ignore[arg-type]
        gemini_api_key="unused",  # type: ignore[arg-type]
        gemini_model="unused",
        image_store=ImageStoreBackend.MEMORY,
        assessment_store=AssessmentStoreBackend.MEMORY,
    )
    document = create_app(settings=settings).openapi()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
