# [See](https://just.systems/man/en/settings.html#shell) for more shell options
set shell := ["zsh", "-uc"]

set dotenv-load := true

[group("Application")]
[doc("Start the API")]
start:
    source .venv/bin/activate && uv run python -m src.main

[group("Code Quality")]
[doc("Lint the API code")]
lint:
    source .venv/bin/activate && ruff check .

[group("Code Quality")]
[doc("Lint and fix the API code")]
lint-fix:
    source .venv/bin/activate && ruff check --fix .

[group("Code Quality")]
[doc("Format the API code")]
format:
    source .venv/bin/activate && ruff format .
