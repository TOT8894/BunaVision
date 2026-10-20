# ============================================================
# Backend service image (split from the old monolith root Dockerfile).
# Builds ONLY the backend API. The public app currently lives at
# backend/app/api/main.py (module: app.api.main:app). The backend calls the
# vision service over HTTP — set the vision base URL via environment.
# ============================================================
FROM python:3.11-slim

WORKDIR /backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# NOTE: app entry currently app/api/main.py. Imports still reference the old
# monolith layout — see the migration header in that file before running.
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
