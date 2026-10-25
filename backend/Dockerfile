FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py ./
COPY config ./config
COPY apps ./apps

# collectstatic needs the required settings to exist; these dummy values are build-time only.
RUN SECRET_KEY=build ALLOWED_HOSTS=build DATABASE_URL=sqlite:///build.db VISION_SERVICE_URL=http://build \
    GEMINI_API_KEY=build GEMINI_MODEL=build IMAGE_STORE=memory python manage.py collectstatic --noinput

RUN useradd --system --uid 10001 bunavision
USER bunavision

EXPOSE 8000
# workers x threads is the concurrency cap (keep it equal to WEB_CONCURRENCY x GUNICORN_THREADS).
# The timeout must exceed the vision + Gemini timeouts. Run `manage.py migrate` as a separate
# release step, never on container start.
ENV WEB_CONCURRENCY=2 GUNICORN_THREADS=4
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --worker-class gthread --workers $WEB_CONCURRENCY --threads $GUNICORN_THREADS --timeout 120"]
