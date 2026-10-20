# ============================================================
# Vision service image (split from the old monolith root Dockerfile).
# Builds ONLY the vision service. Entry point is the thin FastAPI wrapper
# in vision/service/ (TODO(vision owner): create the app module, e.g.
# vision.service.main:app). Model weights ship via the image or a mounted
# volume / S3 — decide per docs/MIGRATION.md.
# ============================================================
FROM python:3.11-slim

WORKDIR /vision

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000

# TODO(vision owner): point this at the thin service wrapper once implemented.
CMD ["uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "9000"]
