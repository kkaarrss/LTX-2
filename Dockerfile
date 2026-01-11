FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY packages ./packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY templates ./templates
COPY static ./static

EXPOSE 8000

ENV GUNICORN_WORKERS=1 \
    GUNICORN_TIMEOUT=0

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --timeout ${GUNICORN_TIMEOUT} app:app"]
