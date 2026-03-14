# IT-548 AI Demo

AI-supported IT ticket triage demo built with NiceGUI, PostgreSQL, pgvector, and OpenAI.

## Overview

The app supports three primary flows:

- `/request` lets a user submit a support ticket.
- `/manual` lets staff review tickets and record manual triage.
- `/ai-process` runs OpenAI-backed triage with retrieval over knowledge-base chunks and similar tickets.

AI triage now uses OpenAI only:

- embeddings: `text-embedding-3-small`
- vector size: `1536`
- structured triage: OpenAI Responses API with strict JSON schema output

## AI Triage Output

The AI result stored on each ticket includes:

- `category`
- `priority`
- `department`
- `ai_summary`
- `ai_recommended_action`
- `ai_missing_information`
- `ai_reasoning`
- `ai_confidence`
- `ai_processing_ms`
- `ai_trace`

Supported AI categories:

- `network`
- `account_access`
- `password_reset`
- `hardware_issue`
- `software_issue`
- `printer_issue`
- `email_issue`
- `security_concern`
- `student_device`
- `classroom_technology`
- `unknown`

Supported departments:

- `helpdesk`
- `network_team`
- `device_support`
- `systems_admin`
- `security_team`

## Data Model

`ticket`

- requestor and ticket details
- workflow status
- manual triage fields
- AI triage fields and retrieval trace

`kb_chunk`

- source text
- metadata
- `vector(1536)` embedding

`ticket_embedding`

- normalized ticket text
- `vector(1536)` embedding

## Requirements

- Python `3.13.x`
- `uv`
- `just`
- Docker for the local Postgres/pgvector stack
- an OpenAI API key

## Setup

```bash
just setup
```

If you want dev tools too:

```bash
just setup-dev
```

## Environment

The app reads settings from `.env`.

Required OpenAI settings:

- `OPENAI_API_KEY`
- `OPENAI_CHAT_MODEL`
- `OPENAI_EMBEDDING_MODEL`

Optional OpenAI settings:

- `OPENAI_TIMEOUT_SECONDS` default `60`
- `OPENAI_MAX_RETRIES` default `2`

Database settings:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

Other app settings:

- `APP_NAME`
- `APP_ENV`
- `SESSION_KEY`
- `LOG_FILE`
- `LOG_LEVEL`
- `LOG_FILE_ROTATION`

Recommended defaults:

```env
OPENAI_CHAT_MODEL=gpt-4.1-nano
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TIMEOUT_SECONDS=60
OPENAI_MAX_RETRIES=2
```

## Running

Without Docker:

```bash
just start
```

With Docker:

```bash
just build
just up
```

Startup behavior:

- runs Alembic migrations
- seeds mock tickets
- seeds KB chunks
- regenerates ticket embeddings so retrieval stays aligned with the active OpenAI embedding model

## Architecture

AI triage flow:

```text
Ticket selected for AI triage
    -> build query text
    -> create OpenAI embedding
    -> search KB chunks in pgvector
    -> search similar tickets in pgvector
    -> send strict JSON-schema triage request to OpenAI
    -> persist AI result fields, trace, and processing time
    -> refresh ticket embedding
```

The retrieval layer remains local to PostgreSQL. Only the embedding and triage model calls go to OpenAI.

## Troubleshooting

- If startup fails, verify Postgres is reachable and migrations can run.
- If AI calls fail, verify `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_TIMEOUT_SECONDS`, and `OPENAI_MAX_RETRIES`.
- If retrieval quality looks wrong after a migration or model change, rerun startup seed or regenerate embeddings so `kb_chunk` and `ticket_embedding` rows are repopulated at `1536` dimensions.
- If embedding requests fail, use an OpenAI embedding model compatible with native `1536`-dimension output such as `text-embedding-3-small`.
