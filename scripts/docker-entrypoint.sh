#!/bin/sh
set -eu

POSTGRES_WAIT_TIMEOUT="${POSTGRES_WAIT_TIMEOUT:-60}"
POSTGRES_WAIT_INTERVAL="${POSTGRES_WAIT_INTERVAL:-1}"

echo "Waiting for postgres to accept connections..."

export POSTGRES_WAIT_TIMEOUT
export POSTGRES_WAIT_INTERVAL

uv run --no-sync python - <<'PY'
import asyncio
import os
import sys
import time

import asyncpg


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    print(f"Missing required environment variable: {name}", file=sys.stderr)
    raise SystemExit(1)


async def wait_for_postgres() -> None:
    host = os.getenv("DB_HOST", "postgres")
    port = int(os.getenv("DB_PORT", "5432"))
    user = require_env("DB_USER")
    password = require_env("DB_PASSWORD")
    database = require_env("DB_NAME")
    timeout_seconds = float(os.getenv("POSTGRES_WAIT_TIMEOUT", "60"))
    interval_seconds = float(os.getenv("POSTGRES_WAIT_INTERVAL", "1"))
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        connection = None
        try:
            connection = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                timeout=min(5.0, interval_seconds),
            )
            await connection.execute("SELECT 1")
            print(f"Postgres is ready at {host}:{port}/{database}")
            return
        except (OSError, asyncpg.PostgresError) as exc:
            last_error = exc
            await asyncio.sleep(interval_seconds)
        finally:
            if connection is not None:
                await connection.close()

    print(
        f"Timed out after {timeout_seconds}s waiting for postgres at "
        f"{host}:{port}/{database}. Last error: {last_error}",
        file=sys.stderr,
    )
    raise SystemExit(1)


asyncio.run(wait_for_postgres())
PY

exec "$@"
