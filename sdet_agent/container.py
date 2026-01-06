from __future__ import annotations

from pathlib import Path
from typing import List

from .plan import ContainerPlan


PYTHON_UV_DOCKERFILE_TEMPLATE = """FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* requirements.txt* ./
RUN if [ -f uv.lock ]; then uv sync --frozen --system; else uv pip install --system -r requirements.txt; fi
COPY . .
CMD ["python", "app_entry_point.py"]
"""


def _format_cmd(cmd: List[str]) -> str:
    # Represent the command as a JSON-like array for Docker CMD
    import json

    return json.dumps(cmd)


def ensure_dockerfile(repo_root: Path, agent_dir: Path, container_plan: ContainerPlan) -> Path:
    """Ensure .agent/Dockerfile exists and matches the given plan.

    Uses the mandatory Python+uv template and adjusts the CMD line.
    """

    agent_dir.mkdir(parents=True, exist_ok=True)
    dockerfile_path = agent_dir / "Dockerfile"

    content = PYTHON_UV_DOCKERFILE_TEMPLATE
    cmd_str = _format_cmd(container_plan.cmd)
    lines = []
    for line in content.splitlines():
        if line.startswith("CMD "):
            lines.append(f"CMD {cmd_str}")
        else:
            lines.append(line)
    dockerfile_path.write_text("\n".join(lines) + "\n")
    return dockerfile_path
