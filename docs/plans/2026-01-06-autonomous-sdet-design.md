# Autonomous SDET Agent Design

**Goal:** Build a Python (uv-based) CLI tool that acts as an Autonomous SDET (Software Development Engineer in Test) agent for this repository, following the Superpowers Loop (Observe → Plan → Act → Reflect) to analyze code changes, containerize the application, generate and execute an E2E test plan, and report results.

**Context:**
- Repo currently has minimal content; future state may include Python and/or Node apps.
- We must enforce tech constraints: Python via `uv`; Node via `pnpm`.
- We must integrate with Docker and respect mandatory Dockerfile templates.
- The agent is primarily a local CLI but should structure logic so a Claude Agent SDK wrapper can invoke the same core steps.

## Architecture Overview

The system is a Python package (e.g. `sdet_agent/`) with a CLI entry point. It orchestrates four phases, mirroring the Superpowers Loop:

1. Observe
   - Inspect `git diff --name-only <base>...HEAD` to determine impacted files.
   - Discover project structure (Python, Node, other) and detect Application Type:
     - Web App: e.g. FastAPI/Flask/Django, or Node web frameworks.
     - CLI/API: pure Python CLI, background service, or HTTP API without browser UI.
   - Identify likely entry point:
     - Python: heuristics over `pyproject.toml`, `setup.cfg`, common filenames (`app.py`, `main.py`, `manage.py`), or ASGI/WSGI apps.
     - Node: `package.json` `scripts.start` / `main` fields.

2. Plan
   - Based on observed Application Type and git diff, generate:
     - A **containerization plan**: which Docker template (Python/uv vs Node/pnpm), expected base image, copy patterns, and CMD/entrypoint.
     - An **E2E test plan** focusing on changed areas:
       - For Web Apps: user flows (pages, forms, navigation) that touch affected modules.
       - For CLI/API: commands or HTTP endpoints exercised with varied inputs.
   - Represent the plan as structured data (e.g. Python dataclasses + JSON/YAML), plus a human-readable Markdown description saved under `.agent/reports/`.

3. Act
   - **Containerization**
     - If `.agent/Dockerfile` exists, optionally validate it against constraints.
     - If not, generate `.agent/Dockerfile` using:
       - Template A (Python with uv) when Python project detected.
       - Template B (Node with pnpm) when Node project detected.
     - Adjust CMD line based on discovered entry point (Python module/script or pnpm script).
     - Run `docker build -t test-target -f .agent/Dockerfile ..` (up to 3 attempts), capturing logs.
   - **Test Script Generation**
     - Create `.agent/tests/` directory.
     - Web App:
       - Generate a Playwright script (Python preferred) that:
         - Waits for the containerized service (e.g. `http://localhost:PORT/`).
         - Performs 1–3 key flows derived from the git diff (e.g. page loads, form submissions).
       - Assume container is started with `docker run -d -p PORT:PORT test-target`.
     - CLI/API:
       - Generate a Python test runner that:
         - For CLI: invokes `docker run --rm test-target [args]` via `subprocess`, validating stdout/stderr and exit codes.
         - For HTTP API: uses `requests` (or standard library `urllib`) against `localhost:PORT` after `docker run -d -p PORT:PORT`.

4. Reflect
   - Execute the test plan:
     - Start container with appropriate ports.
     - Run generated test scripts.
   - Collect artifacts:
     - Test outcomes (pass/fail, assertions).
     - Docker logs (truncated to a reasonable size).
     - Any exceptions, stack traces, or HTTP error responses.
   - Stop and remove the container.
   - Generate a Markdown report summarizing:
     - Impacted Areas (from diff and Application Type).
     - Test Strategy Used (web vs CLI/API, toolchain).
     - Pass/Fail Status and coverage notes.
     - Critical Logs/Errors, with hints for next debugging steps.

## Components

- `sdet_agent/cli.py`
  - CLI entry point (e.g. `python -m sdet_agent` or console script) with a `run` command.
  - Parses optional arguments: base branch, app type override, port, entry point hints, dry-run.

- `sdet_agent/observe.py`
  - Functions to:
    - Run git diff (with sensible fallback when `main` doesnt exist).
    - Analyze filesystem and configuration files to infer Application Type and entry point.
    - Return a structured `Observation` object (dataclass).

- `sdet_agent/plan.py`
  - Translates `Observation` into:
    - `ContainerPlan` (Docker base, CMD, ports, build context).
    - `TestPlan` (flows, endpoints/commands, inputs/outputs).
  - Persists a Markdown and/or JSON representation under `.agent/`.

- `sdet_agent/container.py`
  - Handles `.agent/Dockerfile` generation using provided templates and the `ContainerPlan`.
  - Executes `docker build` with retry logic (max 3 attempts), returning success/failure plus logs.

- `sdet_agent/tests_gen.py`
  - Creates `.agent/tests/` scripts based on `TestPlan` and Application Type.
  - Ensures scripts are executable and have clear entry points (e.g. `python e2e_web.py`).

- `sdet_agent/runner.py`
  - Orchestrates container run, test execution, log collection, and cleanup.
  - Exposes a single `run_e2e()` function used by the CLI.

- `.agent/`
  - `Dockerfile` (generated if missing).
  - `tests/` (generated scripts).
  - `reports/` (Markdown summaries, logs).

## Error Handling & Safety

- If Application Type cannot be determined confidently, default to CLI/API with conservative behavior and clearly mark uncertainty in reports.
- All subprocess calls (git, docker, pnpm, etc.) capture exit codes and stderr; failures propagate to the final report.
- Respect constraints:
  - Never call `pip` directly; only reference `uv`-based workflows in docs/
  - Never call `npm`/`yarn`; only `pnpm` when Node projects are present.
- Avoid destructive actions: no `docker system prune`, no deleting user files.

## Testing Strategy

- Unit tests (later, if repo grows tests):
  - For planners and observers, using pytest or Pythons stdlib.
- End-to-end validation of this agent itself:
  - Use a sample fixture project (Python CLI or FastAPI app) inside this repo or a subdirectory.
  - Run the agent CLI against that fixture to verify Dockerfile generation, build, and test execution.

