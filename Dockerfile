FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

COPY pyproject.toml /app/
COPY .env.example /app/.env.example
COPY api /app/api
COPY cli /app/cli
COPY engine /app/engine
COPY prompts /app/prompts

RUN pip install --upgrade pip && pip install .

EXPOSE 8080

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
