FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/vision

ENV PYTHONPATH=/app
EXPOSE 9000

CMD ["uvicorn", "vision.service.main:app", "--host", "0.0.0.0", "--port", "9000"]
