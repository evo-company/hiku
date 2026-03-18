# Repository Guidelines

## Overview
- `hiku/` contains the library code.
- `tests/` contains the main test suite.
- `tests_pg/` contains PostgreSQL-backed tests that need a running database.
- `docs/` contains Sphinx documentation sources.
- `examples/` contains sample applications and integrations.

## Environment
- Use Python `3.10+`.
- This project uses `uv` for dependency management and environment sync.
- Prefer `uv run ...` for project commands.

## Setup
- Install dependencies with `uv sync`.
- Add `--group ...` when your task needs test, docs, or examples dependencies.

## Validation
- Run targeted tests first, then broaden only if needed.
- Main tests: `uv run pytest tests`
- PostgreSQL tests: `uv run pytest tests_pg --pg-host=localhost`
- Type checks: `uv run mypy hiku`
- Lint: `uv run flake8`
- Format: `uv run black hiku examples`
- Refresh the lockfile when dependencies change: `uv lock`

## Code Style
- Follow existing Python style and keep changes minimal.
- Black is the formatter target with an 80-character line length.
- Mypy is enforced for `hiku/`; preserve or improve typing in touched code.
- Avoid adding new dependencies unless they are necessary for the task.
- Do not add inline comments unless the surrounding code already uses them or the logic is unusually dense.

## Testing Notes
- `tests_pg/` requires PostgreSQL and is not part of the lightweight path for most changes.
- If you change docs-only files, building docs is usually enough: `uv run sphinx-build -b html docs docs/build`.
- If you change examples, verify the specific example instead of broad unrelated checks.

## Scope Discipline
- Do not edit generated or local-environment artifacts unless the task explicitly requires it.
- Keep output files and local tooling noise out of version control; update `.gitignore` only when new generated files are introduced.
- Do not fix unrelated failures while validating a targeted change; report them instead.
