# Autonomous SDET Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a Python (uv-based) CLI agent that performs Observe → Plan → Act → Reflect for code changes in this repo, containerizes the application, generates and runs E2E tests, and outputs a Markdown report.

**Architecture:** The agent is a Python package `sdet_agent` with submodules for observation, planning, containerization, test generation, and execution. A simple CLI entry point orchestrates the workflow. Artifacts (Dockerfile, tests, reports) live under `.agent/` in the repo.

**Tech Stack:** Python 3.11, uv-compatible layout, Docker CLI, git CLI, (optional) Playwright or simple HTTP requests; no direct `pip`, no `npm`/`yarn`.

---

### Task 1: Scaffold Python package and CLI entry

**Files:**
- Create: `pyproject.toml`
- Create: `sdet_agent/__init__.py`
- Create: `sdet_agent/cli.py`
- Create: `sdet_agent/__main__.py`

**Step 1: Write the failing test**

Create `tests/test_cli_entry.py` with:

```python
import subprocess
import sys
from pathlib import Path


def test_cli_help_runs():
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "sdet_agent", "--help"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Autonomous SDET" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_entry.py::test_cli_help_runs -v`
Expected: FAIL because `sdet_agent` module/CLI does not yet exist.

**Step 3: Write minimal implementation**

Implement `pyproject.toml` with a basic project definition using `sdet_agent` as the main package (no `pip`, compatible with uv), and implement `sdet_agent/cli.py` + `sdet_agent/__main__.py` such that:

```python
# sdet_agent/cli.py
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(description="Autonomous SDET agent CLI")
    parser.add_argument("command", nargs="?", default="run", help="Command to execute")
    args = parser.parse_args(argv)
    if args.command in ("-h", "--help", "help"):
        parser.print_help()
        return 0
    # For now, just print a placeholder
    print("Autonomous SDET agent - run")
    return 0
```

```python
# sdet_agent/__main__.py
from .cli import main

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
```

Ensure the help text contains the phrase "Autonomous SDET".

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_entry.py::test_cli_help_runs -v`
Expected: PASS.

**Step 5: (Optional) Commit**

```bash
git add pyproject.toml sdet_agent tests/test_cli_entry.py
git commit -m "feat: scaffold Autonomous SDET CLI"
```

---

### Task 2: Implement Observe phase (git diff + project scan)

**Files:**
- Create: `sdet_agent/observe.py`
- Modify: `sdet_agent/cli.py`
- Create: `tests/test_observe.py`

**Step 1: Write the failing test**

In `tests/test_observe.py`:

```python
from pathlib import Path

from sdet_agent import observe


def test_observation_infers_basic_app_type(tmp_path, monkeypatch):
    # Create a fake repo with a simple Python CLI entry
    (tmp_path / "app.py").write_text("print('hello')\n")

    # Monkeypatch git diff call to return an empty diff
    def fake_run_git_diff(base):  # noqa: ARG001
        return []

    monkeypatch.setattr(observe, "run_git_diff", fake_run_git_diff)

    obs = observe.observe_repository(tmp_path, base_branch="main")

    assert obs.app_type == "python-cli"
    assert obs.entry_point == "app.py"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_observe.py::test_observation_infers_basic_app_type -v`
Expected: FAIL because `sdet_agent.observe` and its functions/types do not exist.

**Step 3: Write minimal implementation**

Implement in `sdet_agent/observe.py`:

- A dataclass `Observation` with fields like `app_type: str`, `entry_point: str | None`, `changed_files: list[str]`.
- A function `run_git_diff(base_branch: str) -> list[str]` that executes `git diff --name-only base_branch...HEAD` (falling back to `git diff --name-only` if that fails) in the given repo.
- A function `infer_app_type_and_entry(repo_root: Path, changed_files: list[str]) -> tuple[str, str | None]` that:
  - If `app.py` exists at repo root, sets `app_type="python-cli"` and `entry_point="app.py"`.
  - (Future extension for web and Node, but keep minimal now.)
- A function `observe_repository(repo_root: Path, base_branch: str) -> Observation` that:
  - Calls `run_git_diff(base_branch)`.
  - Calls `infer_app_type_and_entry`.
  - Returns an `Observation` instance.

Update `sdet_agent/cli.py` `main()` to:
- Accept an optional `--base` argument for base branch (default: `main`).
- When command is `run`, call `observe_repository(Path.cwd(), base_branch)` and print a short summary including `app_type`.

**Step 4: Run test to verify it passes**

Run:
- `pytest tests/test_observe.py::test_observation_infers_basic_app_type -v`
- `pytest tests/test_cli_entry.py::test_cli_help_runs -v`
Expected: both PASS.

**Step 5: (Optional) Commit**

```bash
git add sdet_agent/observe.py sdet_agent/cli.py tests/test_observe.py
git commit -m "feat: add observe phase for Autonomous SDET"
```

---

### Task 3: Implement Plan phase (container + test plan generation)

**Files:**
- Create: `sdet_agent/plan.py`
- Modify: `sdet_agent/cli.py`
- Create: `tests/test_plan.py`

**Step 1: Write the failing test**

In `tests/test_plan.py`:

```python
from sdet_agent.observe import Observation
from sdet_agent import plan


def test_plan_creates_basic_container_and_test_plan(tmp_path):
    obs = Observation(
        app_type="python-cli",
        entry_point="app.py",
        changed_files=["app.py"],
    )

    container_plan, test_plan = plan.create_plans(obs, repo_root=tmp_path)

    assert container_plan.base_image.startswith("python:3.11")
    assert container_plan.cmd == ["python", "app.py"]
    assert test_plan.kind == "cli"
    assert any("app.py" in flow.description for flow in test_plan.flows)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_plan.py::test_plan_creates_basic_container_and_test_plan -v`
Expected: FAIL because `sdet_agent.plan` does not exist.

**Step 3: Write minimal implementation**

In `sdet_agent/plan.py`:
- Define dataclasses:
  - `ContainerPlan` with fields like `base_image: str`, `cmd: list[str]`, `ports: list[int]`.
  - `TestFlow` with `description: str`.
  - `TestPlan` with `kind: str` (e.g. `"cli"` or `"web"`), `flows: list[TestFlow]`.
- Implement `create_plans(observation: Observation, repo_root: Path) -> tuple[ContainerPlan, TestPlan]`:
  - For `app_type == "python-cli"`:
    - `ContainerPlan(base_image="python:3.11-slim-bookworm", cmd=["python", observation.entry_point], ports=[])`.
    - `TestPlan(kind="cli", flows=[TestFlow(description=f"Run {observation.entry_point} and assert success")])`.

Optionally, write a small function in `plan.py` to persist a Markdown summary under `.agent/reports/plan.md`.

Update `sdet_agent/cli.py` `main()` `run` path to:
- After observation, call `create_plans`.
- Print a short summary, e.g. base image and test plan kind.

**Step 4: Run test to verify it passes**

Run:
- `pytest tests/test_plan.py::test_plan_creates_basic_container_and_test_plan -v`
- `pytest tests/test_observe.py::test_observation_infers_basic_app_type -v`
- `pytest tests/test_cli_entry.py::test_cli_help_runs -v`
Expected: all PASS.

**Step 5: (Optional) Commit**

```bash
git add sdet_agent/plan.py sdet_agent/cli.py tests/test_plan.py
git commit -m "feat: add plan phase for container and test planning"
```

---

### Task 4: Implement Act phase – Dockerfile generation and docker build

**Files:**
- Create: `sdet_agent/container.py`
- Modify: `sdet_agent/cli.py`
- Create: `.agent/.gitkeep` (to ensure directory exists if desired)
- Create: `tests/test_container.py`

**Step 1: Write the failing test**

In `tests/test_container.py`:

```python
from pathlib import Path

from sdet_agent.plan import ContainerPlan
from sdet_agent import container


def test_generate_python_cli_dockerfile(tmp_path):
    repo_root = tmp_path
    (repo_root / "app.py").write_text("print('hello')\n")
    agent_dir = repo_root / ".agent"
    agent_dir.mkdir()

    plan = ContainerPlan(
        base_image="python:3.11-slim-bookworm",
        cmd=["python", "app.py"],
        ports=[],
    )

    dockerfile_path = container.ensure_dockerfile(repo_root, agent_dir, plan)

    content = dockerfile_path.read_text()
    assert "FROM python:3.11-slim-bookworm" in content
    assert "uv" in content  # must use uv
    assert "CMD [\"python\", \"app.py\"]" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_container.py::test_generate_python_cli_dockerfile -v`
Expected: FAIL because `sdet_agent.container` is missing.

**Step 3: Write minimal implementation**

In `sdet_agent/container.py`:
- Implement `ensure_dockerfile(repo_root: Path, agent_dir: Path, container_plan: ContainerPlan) -> Path` that:
  - Creates `agent_dir` if it doesn\'t exist.
  - Writes `.agent/Dockerfile` with the **Python with uv** template:

    ```dockerfile
    FROM python:3.11-slim-bookworm
    COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
    WORKDIR /app
    COPY pyproject.toml uv.lock* requirements.txt* ./
    RUN if [ -f uv.lock ]; then uv sync --frozen --system; else uv pip install --system -r requirements.txt; fi
    COPY . .
    CMD ["python", "app_entry_point.py"]
    ```

  - Replace the CMD line with the one from `container_plan.cmd`, serialised as a JSON array.

(Optionally, add a small helper function that builds the image with `docker build -t test-target -f .agent/Dockerfile ..`, but because docker may not be available in tests, we won\'t assert a real build here.)

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_container.py::test_generate_python_cli_dockerfile -v`
Expected: PASS.

**Step 5: (Optional) Commit**

```bash
git add sdet_agent/container.py .agent tests/test_container.py
git commit -m "feat: generate Dockerfile for python-cli app using uv"
```

---

### Task 5: Implement Act & Reflect – E2E test runner and Markdown report

**Files:**
- Create: `sdet_agent/runner.py`
- Modify: `sdet_agent/cli.py`
- Create: `.agent/tests/e2e_cli.py` (template generated by code)
- Create: `tests/test_runner_smoke.py`

**Step 1: Write the failing test**

In `tests/test_runner_smoke.py`:

```python
from pathlib import Path

from sdet_agent.observe import Observation
from sdet_agent.plan import ContainerPlan, TestPlan, TestFlow
from sdet_agent import runner


def test_runner_generates_report_without_docker(tmp_path, monkeypatch):
    repo_root = tmp_path
    (repo_root / "app.py").write_text("print('hello')\n")
    agent_dir = repo_root / ".agent"

    obs = Observation(app_type="python-cli", entry_point="app.py", changed_files=["app.py"])
    container_plan = ContainerPlan(
        base_image="python:3.11-slim-bookworm",
        cmd=["python", "app.py"],
        ports=[],
    )
    test_plan = TestPlan(kind="cli", flows=[TestFlow(description="Run app.py")])

    # Monkeypatch docker-related calls so the test doesn\'t require docker
    monkeypatch.setattr(runner, "build_image", lambda *a, **k: False)
    monkeypatch.setattr(runner, "run_container_and_tests", lambda *a, **k: (False, "", "docker not available"))

    report_path = runner.run_e2e(repo_root, agent_dir, obs, container_plan, test_plan)

    report_text = report_path.read_text()
    assert "Impacted Areas" in report_text
    assert "Pass/Fail Status" in report_text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_runner_smoke.py::test_runner_generates_report_without_docker -v`
Expected: FAIL because `sdet_agent.runner` is missing.

**Step 3: Write minimal implementation**

In `sdet_agent/runner.py`:
- Implement `run_e2e(repo_root: Path, agent_dir: Path, obs: Observation, container_plan: ContainerPlan, test_plan: TestPlan) -> Path` that:
  - Ensures `agent_dir` and `agent_dir / "reports"` exist.
  - Calls stubbed `build_image` and `run_container_and_tests` (definable for now as always failing or delegated to monkeypatches in tests).
  - Writes a Markdown report file under `agent_dir / "reports" / "latest.md"` with sections:
    - "Impacted Areas"
    - "Test Strategy Used"
    - "Pass/Fail Status"
    - "Critical Logs"
  - Returns the report path.

You may also implement simple default `build_image` and `run_container_and_tests` functions for later real-world use.

Update `sdet_agent/cli.py` `run` path to:
- Wire together Observe → Plan → Act → Reflect:
  - Call `observe_repository` → `create_plans` → `ensure_dockerfile` → `run_e2e`.
  - Print the report path at the end.

**Step 4: Run test to verify it passes**

Run:
- `pytest tests/test_runner_smoke.py::test_runner_generates_report_without_docker -v`
- Plus all previous tests.
Expected: all PASS (with docker behavior mocked in this test).

**Step 5: (Optional) Commit**

```bash
git add sdet_agent/runner.py sdet_agent/cli.py .agent tests/test_runner_smoke.py
git commit -m "feat: add E2E runner and Markdown report generation"
```

---

### Task 6: Wire everything into a single CLI command

**Files:**
- Modify: `sdet_agent/cli.py`
- Optionally modify tests for end-to-end coverage

**Step 1: Write the failing test**

Extend `tests/test_cli_entry.py` with:

```python
from pathlib import Path


def test_cli_run_prints_report_path(tmp_path, monkeypatch):
    # Minimal repo with app.py
    (tmp_path / "app.py").write_text("print('hello')\n")

    # Monkeypatch heavy operations
    from sdet_agent import runner as runner_mod
    monkeypatch.setattr(runner_mod, "run_e2e", lambda *a, **k: tmp_path / ".agent" / "reports" / "latest.md")

    result = subprocess.run(
        [sys.executable, "-m", "sdet_agent", "run"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert ".agent/reports/latest.md" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_entry.py::test_cli_run_prints_report_path -v`
Expected: FAIL because `cli.run` path does not yet print the report path exactly.

**Step 3: Write minimal implementation**

Adjust `sdet_agent/cli.py` so that when invoked as `python -m sdet_agent run`:
- It orchestrates Observe → Plan → Act → Reflect.
- Prints a line containing the relative report path, e.g. `"Report written to .agent/reports/latest.md"`.

**Step 4: Run test to verify it passes**

Run:

```bash
pytest -v
```

Expected: all tests PASS.

**Step 5: (Optional) Commit**

```bash
git add sdet_agent tests pyproject.toml .agent
git commit -m "feat: wire Autonomous SDET CLI end-to-end"
```

