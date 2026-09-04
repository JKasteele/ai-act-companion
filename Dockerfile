# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Keep Python lean and unbuffered for clean container logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application.
COPY app ./app
COPY static ./static
COPY examples ./examples

# Assessments are written here at runtime (mount a volume to persist). Run as a
# dedicated unprivileged user; the application does not need root privileges.
RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p data \
    && chown -R app:app /app
USER app

# The AI layer defaults to the 'manual' provider in a container, since a local
# Ollama runs on the host. Override with -e LLM_PROVIDER=ollama and
# -e OLLAMA_HOST=http://host.docker.internal:11434 if desired.
ENV LLM_PROVIDER=manual

# Honour an optional $PORT override while defaulting to 8000, which matches the
# documented Hugging Face Space card. The small shell wrapper expands the
# variable and `exec` preserves container signal handling.
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
