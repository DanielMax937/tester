from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Tuple

from .observe import Observation
from .plan import ContainerPlan, TestPlan


def build_image(repo_root: Path, agent_dir: Path, container_plan: ContainerPlan) -> bool:  # noqa: ARG001
    """Build the docker image `test-target` using the .agent/Dockerfile.

    This follows the required command pattern:
    `docker build -t test-target -f .agent/Dockerfile ..`

    We run it from the project root with the parent directory as context,
    so the Dockerfile's `COPY . .` behaves as expected relative to the
    repository layout.
    """

    dockerfile_path = agent_dir / "Dockerfile"
    # Context directory: parent of repo_root, matching the `..` pattern.
    context_dir = repo_root.parent

    result = subprocess.run(
        [
            "docker",
            "build",
            "-t",
            "test-target",
            "-f",
            str(dockerfile_path),
            str(context_dir),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    # We do not raise here; callers examine the boolean and, if desired,
    # surface stderr/stdout in reports.
    return result.returncode == 0


def _run_subprocess(args, cwd: Path) -> Tuple[int, str, str]:
    """Run a subprocess and capture (returncode, stdout, stderr)."""

    proc = subprocess.run(
        list(args),
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_container_and_tests(
    repo_root: Path,
    agent_dir: Path,
    container_plan: ContainerPlan,
    test_plan: TestPlan,
) -> Tuple[bool, str, str]:
    """Run the container and execute host-side tests.

    Behaviour:
    - For CLI apps (kind == "cli"):
      - If `.agent/tests/e2e_cli.py` exists, run it directly. It is
        expected to invoke `docker run` as needed.
      - Otherwise, fall back to `docker run --rm test-target` and treat
        exit code and output as the E2E result.
    - For web apps (ports specified or kind == "web"):
      - Start a detached container with appropriate `-p PORT:PORT` flags.
      - If `.agent/tests/e2e_web.py` exists, run it against
        `http://localhost:PORT` (script decides details).
      - Finally, stop the container.
    """

    tests_dir = agent_dir / "tests"
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def record(rc: int, out: str, err: str) -> Tuple[bool, str, str]:
        stdout_chunks.append(out)
        stderr_chunks.append(err)
        return rc == 0, "".join(stdout_chunks), "".join(stderr_chunks)

    # CLI path
    if test_plan.kind == "cli" and not container_plan.ports:
        e2e_cli = tests_dir / "e2e_cli.py"
        if e2e_cli.exists():
            rc, out, err = _run_subprocess(["python", str(e2e_cli)], cwd=repo_root)
            return record(rc, out, err)

        # Fallback: run the image directly
        rc, out, err = _run_subprocess(["docker", "run", "--rm", "test-target"], cwd=repo_root)
        return record(rc, out, err)

    # Web / port-mapped path
    ports = container_plan.ports or []
    is_web = test_plan.kind == "web" or bool(ports)

    if is_web:
        container_name = "test-runner-container"
        port_args: list[str] = []
        for port in ports:
            port_args.extend(["-p", f"{port}:{port}"])

        # Start container detached
        rc_start, out_start, err_start = _run_subprocess(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                container_name,
                *port_args,
                "test-target",
            ],
            cwd=repo_root,
        )
        stdout_chunks.append(out_start)
        stderr_chunks.append(err_start)

        if rc_start != 0:
            # Could not even start the container
            return False, "".join(stdout_chunks), "".join(stderr_chunks)

        # Run web E2E script if present
        e2e_web = tests_dir / "e2e_web.py"
        if e2e_web.exists():
            rc_test, out_test, err_test = _run_subprocess(["python", str(e2e_web)], cwd=repo_root)
            stdout_chunks.append(out_test)
            stderr_chunks.append(err_test)
        else:
            # No dedicated script; treat successful startup as tentative success
            rc_test = 0

        # Tear down container (best-effort)
        _run_subprocess(["docker", "stop", container_name], cwd=repo_root)

        return rc_test == 0, "".join(stdout_chunks), "".join(stderr_chunks)

    # Fallback: treat as CLI without special scripts
    rc, out, err = _run_subprocess(["docker", "run", "--rm", "test-target"], cwd=repo_root)
    return record(rc, out, err)


def run_e2e(
    repo_root: Path,
    agent_dir: Path,
    observation: Observation,
    container_plan: ContainerPlan,
    test_plan: TestPlan,
) -> Path:
    """Run the end-to-end Autonomous SDET flow and write a Markdown report.

    This now performs a real docker build (via `build_image`) and, on
    success, runs the appropriate container + tests via
    `run_container_and_tests`. The report captures success status and
    aggregated stdout/stderr from these steps.
    """

    reports_dir = agent_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Build image first
    build_ok = build_image(repo_root, agent_dir, container_plan)

    if not build_ok:
        success = False
        stdout = ""
        stderr = "docker build failed or docker daemon unavailable"
    else:
        success, stdout, stderr = run_container_and_tests(repo_root, agent_dir, container_plan, test_plan)

    report_path = reports_dir / "latest.md"
    lines = [
        "# Autonomous SDET Report",
        "",
        "## Impacted Areas",
        f"- App type: {observation.app_type}",
        f"- Entry point: {observation.entry_point}",
        f"- Changed files: {', '.join(observation.changed_files) if observation.changed_files else 'None'}",
        "",
        "## Test Strategy Used",
        f"- Kind: {test_plan.kind}",
        f"- Flows: {[flow.description for flow in test_plan.flows]}",
        "",
        "## Pass/Fail Status",
        f"- Success: {success}",
        "",
        "## Critical Logs",
        f"- STDOUT: {stdout[:2000]}",
        f"- STDERR: {stderr[:2000]}",
        "",
    ]
    report_path.write_text("\n".join(lines) + "\n")
    return report_path
