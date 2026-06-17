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

# Assessments are written here at runtime (mount a volume to persist).
RUN mkdir -p data

# The AI layer defaults to the 'manual' provider in a container, since a local
# Ollama runs on the host. Override with -e LLM_PROVIDER=ollama and
# -e OLLAMA_HOST=http://host.docker.internal:11434 if desired.
ENV LLM_PROVIDER=manual

# Honour $PORT so the same image runs locally (8000) and on hosts that inject a
# port, e.g. Hugging Face Spaces sets PORT=7860. Shell form so $PORT expands.
EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
