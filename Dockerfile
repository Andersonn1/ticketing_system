FROM ghcr.io/astral-sh/uv:python3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_NO_CACHE=1

WORKDIR /app

RUN addgroup -g 10001 appuser && \
    adduser -D -H -u 10001 -G appuser appuser


COPY pyproject.toml uv.lock /app/
COPY alembic.ini /app/alembic.ini
COPY src /app/src
COPY alembic /app/alembic
COPY data /app/data

RUN uv sync --frozen --no-dev \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["uv", "run", "--no-sync", "python", "-m", "src.main"]
