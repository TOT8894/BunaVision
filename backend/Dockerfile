FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
COPY app ./app

RUN useradd --system --uid 10001 bunavision
USER bunavision

EXPOSE 8000
# Run `alembic upgrade head` as a separate release step before starting new containers.
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
