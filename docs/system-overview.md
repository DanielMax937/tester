# Autonomous SDET Agent – System Overview

## Purpose

The Autonomous SDET (Software Development Engineer in Test) agent is a Python-based CLI tool that analyzes this repository, infers the application type, plans containerization, generates and executes end-to-end (E2E) tests, and produces a Markdown report summarizing results. It follows the **Superpowers Loop** (Observe → Plan → Act → Reflect) and respects strict tooling constraints (Python via `uv`, Node.js via `pnpm`).

## High-Level Flow

1. **Observe**
   - Runs `git diff --name-only <base>...HEAD` to determine changed files.
   - Inspects the project structure to infer **Application Type** and **entry point**:
     - `python-cli`: simple Python CLI with `app.py` at repo root.
     - `python-web`: web service detected via FastAPI/Flask/uvicorn/gunicorn patterns.
     - `unknown`: fallback when nothing clear is found.

2. **Plan**
   - Translates the `Observation` into:
     - A **ContainerPlan** (base image, command, ports).
     - A **TestPlan** (kind and flows).
   - Examples:
     - `python-cli`: `base_image = python:3.11-slim-bookworm`, `cmd = ["python", "app.py"]`, no ports.
     - `python-web`: same base image/command, default port `8000` mapped (`-p 8000:8000`) and HTTP-oriented flows.

3. **Act**
   - Ensures `.agent/Dockerfile` exists using the mandatory **Python + uv** template:
     - `FROM python:3.11-slim-bookworm`.
     - Copies `pyproject.toml`, `uv.lock*`, `requirements.txt*`.
     - Installs dependencies via `uv sync --frozen --system` or `uv pip install --system -r requirements.txt`.
     - Adjusts `CMD` to match the planned entry point.
   - Builds the image:
     - `docker build -t test-target -f .agent/Dockerfile ..`.
   - Runs the container and tests:
     - **CLI**: runs `.agent/tests/e2e_cli.py` if present, otherwise `docker run --rm test-target`.
     - **Web**: runs `docker run -d --rm --name test-runner-container -p PORT:PORT test-target` and then `.agent/tests/e2e_web.py` if present, stopping the container afterward.

4. **Reflect**
   - Aggregates success/failure from docker build and test execution.
   - Captures stdout/stderr from key commands.
   - Writes a Markdown report to `.agent/reports/latest.md` including:
     - Impacted areas (app type, entry point, changed files).
     - Test strategy (CLI vs web, flows).
     - Pass/fail status.
     - Critical logs (truncated docker/test output).

## Key Components

- `sdet_agent/cli.py`
  - CLI entry point (`python -m sdet_agent` or `sdet-agent`).
  - Orchestrates Observe → Plan → Act → Reflect.
  - Supports options like `--base` (git base branch) and `--dry-run` (plan only).

- `sdet_agent/observe.py`
  - Defines `Observation` dataclass.
  - Implements `run_git_diff` and `observe_repository`.
  - Detects `python-cli` vs `python-web` via files and framework hints.

- `sdet_agent/plan.py`
  - Defines `ContainerPlan`, `TestFlow`, and `TestPlan` dataclasses.
  - Implements `create_plans` for CLI and web scenarios.

- `sdet_agent/container.py`
  - Generates `.agent/Dockerfile` from the Python+uv template.
  - Rewrites the `CMD` line using the planned command.

- `sdet_agent/runner.py`
  - `build_image`: runs `docker build -t test-target -f .agent/Dockerfile ..`.
  - `run_container_and_tests`: runs containers and host-side E2E tests (CLI and web with port mapping).
  - `run_e2e`: glues everything together and writes the final Markdown report.

## Directories and Files

- `pyproject.toml` – Python project metadata (uv-compatible).
- `sdet_agent/` – Core agent implementation.
- `tests/` – Unit and integration tests covering CLI, planning, containerization, and reporting.
- `.agent/` – Agent artifacts:
  - `Dockerfile` – Generated container definition.
  - `tests/` – E2E scripts (e.g. `e2e_cli.py`, `e2e_web.py`).
  - `reports/latest.md` – Latest E2E execution report.

## Usage Summary

- Dry-run (no docker required):

  ```bash
  python -m sdet_agent run --dry-run
  ```

- Full run (with Docker available):

  ```bash
  python -m sdet_agent run
  ```

  This will build the image, run the appropriate E2E tests for the detected app type, and write a report to `.agent/reports/latest.md`.
