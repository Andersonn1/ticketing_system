# [See](https://just.systems/man/en/settings.html#shell) for more shell options
set shell := ["zsh", "-uc"]

export COMPOSE_BAKE :="1"
export DOCKER_BUILDKIT := "1"

set dotenv-load := true

[private]
default:
    @just --list

[private]
source_venv:
    source .venv/bin/activate

[group("Application Docker Commands")]
[doc("Build the docker images")]
build:
    docker compose build

[group("Application Docker Commands")]
[doc("Stop the docker containers")]
down:
    docker compose down --volumes

[group("Application Docker Commands")]
[doc("Start the application with docker")]
up:
    docker compose up -d

[group("Launch Application")]
[doc("Start the application without docker")]
start: source_venv
    uv run python -m src.main

[group("Project Setup")]
[doc("Bootstrap local dev environment (env files, venv, deps, logs dir)")]
setup:
    ./scripts/setup-env-files.sh
    uv venv
    uv sync
    mkdir -p logs

[group("Project Setup")]
[doc("Install optional development dependency group")]
setup-dev:
    uv sync --group dev

[group("Application Migrations")]
[doc("Create a new database migration")]
migration-new message="auto migration":
    docker exec -it app uv run alembic revision --autogenerate -m "{{message}}"

[group("Code Quality")]
[doc("Lint the API code")]
lint: source_venv
    ruff check .

[group("Code Quality")]
[doc("Lint and fix the API code")]
lint-fix: source_venv
    ruff check --fix .

[group("Code Quality")]
[doc("Format the API code")]
format: source_venv
    ruff format .
