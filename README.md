# IT-548 AI Demo

## Table of Contents

- [IT-548 AI Demo](#it-548-ai-demo)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
    - [App Flow](#app-flow)
    - [Database Schemas](#database-schemas)
    - [LLM Prompt](#llm-prompt)
    - [Tech Stack](#tech-stack)
    - [Dependency Injection Convention](#dependency-injection-convention)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Quick Start](#quick-start)
    - [Environment Configuration](#environment-configuration)
    - [Useful `just` Commands](#useful-just-commands)
    - [Running the App](#running-the-app)
      - [Ensure Ollama Running and Models Are Pulled](#ensure-ollama-running-and-models-are-pulled)
      - [Without Docker](#without-docker)
      - [With Docker (recommended)](#with-docker-recommended)
  - [Troubleshooting](#troubleshooting)

## Project Overview

This repository is an AI-supported IT ticketing demo built with NiceGUI.

### App Flow

```text
Application startup
        |
        v
Run Alembic migrations
        |
Seed tickets from data/MOCK_DATA.json
and seed demo KB chunks
        |
User opens NiceGUI pages
        |
        +--> `/manual` shows ticket table with manual status actions
        |
        +--> `/ai-process` shows the same ticket table plus
              "Run AI on Selected"
        |
AI triage action
        |
        +--> build query text from selected ticket
        +--> embed via Ollama
        +--> search KB chunks and similar tickets in PostgreSQL / pgvector
        +--> request structured JSON triage output from Ollama
        +--> persist summary, response, category, priority,
              next steps, confidence, and retrieval trace
```

### Database Schemas

```text
__Ticket_Table__
  id pk
  requestor_name str
  requestor_email str
  user_role student|faculty|alum|vendor|other
  title str
  description text
  status open|pending|closed
  priority High|Medium|Low
  category Hardware|Software|Network|Security|Other
  ai_summary text nullable
  ai_response text nullable
  ai_next_steps jsonb
  ai_confidence High|Medium|Low nullable
  ai_trace jsonb nullable
  created_at datetime w tz
  updated_at datetime w tz

__Knowledge_Base_Chunks_Table__
  id pk
  source_name str
  chunk_text text
  metadata jsonb
  embedding vector(...)

__Ticket_Embeddings__
  id pk
  ticket_id fk
  combined_text text
  embedding vector(...)
```

### LLM Prompt

```test
You are a school IT help desk assistant.

Return ONLY valid JSON.
Do not include markdown fences or prose before/after the JSON.
Be practical, concise, and grounded in the provided context.
If the context is weak, say so explicitly in the response while still providing next steps.

Ticket:
Requestor: {requestor_name} ({user_role})
Email: {requestor_email}
Title: {title}
Description: {description}

Relevant knowledge base context:
{top_k_chunks}

Similar past tickets:
{top_ticket_matches}

Return JSON with:
category, priority, summary, response, next_steps, confidence
```

### Tech Stack

- [Python 3.13](https://www.python.org/downloads/) (runtime requirement)
- [uv](https://docs.astral.sh/uv/) for Python project/dependency management
- [NiceGUI](https://nicegui.io/) for the web UI
- [Loguru](https://loguru.readthedocs.io/) for structured application logging
- [Just](https://just.systems/man/en/) for command shortcuts
- [Ollama](https://docs.ollama.com/) for local LLm hosting

### Dependency Injection Convention

- Shared runtime services, clients, and app-facing settings providers live in `src/dependencies.py`.
- NiceGUI pages and FastAPI routes should receive app services through `Depends(...)` where the framework supports it.
- Lower-level implementation details such as repositories and session-bound objects stay local unless they become shared composition seams.

## Getting Started

### Prerequisites

- Python installed (3.13.x)
- uv installed (`uv --version`)
- just installed (`just --version`)
- Git installed (`git --version`)
- [Docker](https://docs.docker.com/get-started/get-docker/) installed (`docker --version`)
- [Ollama](https://ollama.com/download) installed (`ollama --version`)

### Quick Start

1. From the repository root, run:

   ```bash
   just setup
   ```

2. Install optional development tools:

   ```bash
   just setup-dev
   ```

3. If you prefer manual setup instead of `just setup`, run:

   ```bash
   uv venv
   uv sync
   ./scripts/setup-env-files.sh
   mkdir -p logs
   ```

### Environment Configuration

Current app settings are loaded from `.env`:

- `APP_NAME` (optional): Friendly app title.
- `APP_ENV` (optional): `develop`, `staging`, or `production`.
- `LOG_FILE` (optional): Log file path. Default is `logs/app.log`.
- `LOG_LEVEL` (optional): Standard log level, e.g. `DEBUG` or `INFO`.
- `LOG_FILE_ROTATION` (optional): Example: `3 days`.
- `SESSION_KEY` (optional but recommended): Secret used by `SessionMiddleware`.
- `CHAT_MODEL` (required): AI model name for your provider.
- `EMBEDDING_MODEL` (required): Embedding model name for Ollama. `EMBED_MODEL` is also accepted.
- `MODEL_PROVIDER` (optional): Provider identifier. Defaults to `ollama`.
- `OLLAMA_BASE_URL` (optional): Ollama base URL. `MODEL_PROVIDER_URL` is also accepted.
- `MODEL_PROVIDER_API_KEY` (optional): Provider API key.
- `DB_NAME` (required): Name of the Postgres database.
- `DB_USER` (required): Postgres username.
- `DB_HOST` (optional): Postgres host. Defaults to `localhost`.
- `DB_PASSWORD` (required): Postgres password.
- `DB_PORT` (optional): Postgres port. Defaults to `5432`.
- `DB_HOST` should be `localhost` for local non-container runs and `postgres` in compose.

Note: the `.env` and `.env.TEMPLATE` can include additional variables; only values read by settings are required.

### Useful `just` Commands

- `just setup`  
  Creates missing env files from templates, creates `.venv`, installs runtime dependencies, and ensures `logs/` exists.
- `just setup-dev`  
  Installs optional development dependencies (`uv sync --group dev`).
- `just start`  
  Runs the app with the configured virtual environment.
- `just lint`  
  Runs `ruff check .` on the project.
- `just lint-fix`  
  Runs `ruff check --fix .`.
- `just format`  
  Runs `ruff format .`.
- `just migration-new "describe schema change"`  
  Creates a new Alembic migration with autogeneration.
- `just down`  
  Stops the docker containers and removes their volumes.
- `alembic upgrade head` runs during application startup via `src.db.migrations` to fail fast if DB or migration state is invalid.

### Running the App

The application automatically runs `alembic upgrade head` during startup and then seeds data from `data/MOCK_DATA.json` using the service-layer repository path. If either migrations or seed processing fail (for example, DB is unreachable or credentials are invalid), startup fails fast.

#### Ensure Ollama Running and Models Are Pulled

```bash
ollama pull qwen3.5:2b
```

```bash
ollama pull nomic-embed-text
```

From project root:

#### Without Docker

```bash
just start
```

or directly:

```bash
uv run python -m src.main
```

#### With Docker (recommended)

```bash
just build
```

```bash
just up
```

```bash
just down
```

> By default, the app runs at `http://127.0.0.1:8080`.

Useful routes:

- `/` home page
- `/manual` manual ticket workflow
- `/ai-process` AI triage workflow
- `/status` health check

## Troubleshooting

- If `just start` fails on Windows, open a Unix-like shell (WSL/Git Bash) because the provided `Justfile` shell is configured for `zsh`.
- If logging does not appear at `logs/app.log`, check write permissions to the configured `LOG_FILE` directory.
- If AI model calls fail, verify `CHAT_MODEL`, `EMBEDDING_MODEL`, `OLLAMA_BASE_URL`, and `MODEL_PROVIDER_API_KEY`.
