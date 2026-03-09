# IT-548 AI Demo

## Table of Contents

- [IT-548 AI Demo](#it-548-ai-demo)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Tech Stack](#tech-stack)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Environment Configuration](#environment-configuration)
  - [Useful `just` Commands](#useful-just-commands)
  - [Running the App](#running-the-app)
    - [Without Docker](#without-docker)
    - [With Docker (recommended)](#with-docker-recommended)
  - [Troubleshooting](#troubleshooting)

## Project Overview

This repository is an AI-supported IT ticketing demo built with NiceGUI.

## Tech Stack

- [Python 3.13](https://www.python.org/downloads/) (runtime requirement)
- [uv](https://docs.astral.sh/uv/) for Python project/dependency management
- [NiceGUI](https://nicegui.io/) for the web UI
- [Loguru](https://loguru.readthedocs.io/) for structured application logging
- [Just](https://just.systems/man/en/) for command shortcuts

## Prerequisites

- Python installed (3.13.x)
- uv installed (`uv --version`)
- just installed (`just --version`)
- Git installed (`git --version`)
- [Docker](https://docs.docker.com/get-started/get-docker/) installed (`docker --version`)

## Quick Start

1. From the repository root, create and activate a virtual environment:

   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Install development tools (optional):

   ```bash
   uv sync --group dev
   ```

4. Copy the environment template and edit values:

   ```bash
   cp .env.TEMPLATE .env
   ```

5. Copy the postgres environment template and edit values:

   ```bash
   cp postgres.env.TEMPLATE postgres.env
   ```

6. Copy the pgadmin environment template and edit values:

   ```bash
   cp pgadmin.env.TEMPLATE pgadmin.env
   ```

7. Ensure the log directory exists if you changed `LOG_FILE` to a nested path:

   ```bash
   mkdir -p logs
   ```

## Environment Configuration

Current app settings are loaded from `.env`:

- `APP_NAME` (optional): Friendly app title.
- `LOG_FILE` (optional): Log file path. Default is `logs/app.log`.
- `LOG_LEVEL` (optional): Standard log level, e.g. `DEBUG` or `INFO`.
- `LOG_FILE_ROTATION` (optional): Example: `3 days`.
- `MODEL` (required): AI model name for your provider.
- `MODEL_PROVIDER` (required): Provider identifier.
- `MODEL_PROVIDER_URL` (required): Provider endpoint URL.
- `MODEL_PROVIDER_API_KEY` (required): Provider API key.
- `DB_NAME` (required): Name of postgres database (Defaults to ticketing_system)
- `DB_USER` (required): Name of postgres database user (Defaults to ticketing_user)
- `DB_PASSWORD` (required): Password to postgres database
- `DB_PORT` (required): Port that postgres is listening on (Defaults to 5432)

Note: the `.env` and `.env.TEMPLATE` can include additional variables; only values read by settings are required.

## Useful `just` Commands

- `just start`  
  Runs the app with the configured virtual environment.
- `just lint`  
  Runs `ruff check .` on the project.
- `just lint-fix`  
  Runs `ruff check --fix .`.
- `just format`  
  Runs `ruff format .`.

## Running the App

From project root:

### Without Docker

```bash
just start
```

or directly:

```bash
uv run python -m src.main
```

### With Docker (recommended)

```bash
just build
```

```bash
just up
```

```bash
just stop # To stop the docker containers
```

> By default, the app runs at `http://127.0.0.1:8080`.

## Troubleshooting

- If `just start` fails on Windows, open a Unix-like shell (WSL/Git Bash) because the provided `Justfile` shell is configured for `zsh`.
- If logging does not appear at `logs/app.log`, check write permissions to the configured `LOG_FILE` directory.
- If AI model calls fail, verify `MODEL`, `MODEL_PROVIDER`, `MODEL_PROVIDER_URL`, and `MODEL_PROVIDER_API_KEY`.
