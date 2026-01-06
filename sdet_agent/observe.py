from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import subprocess


@dataclass
class Observation:
    app_type: str
    entry_point: Optional[str]
    changed_files: List[str]


def run_git_diff(base_branch: str, repo_root: Path) -> List[str]:
    """Return list of changed files relative to base_branch.

    Falls back to plain `git diff --name-only` if the three-dot form fails.
    """

    def _run(args):
        result = subprocess.run(
            args,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        return [line for line in result.stdout.splitlines() if line.strip()]

    changed = _run(["git", "diff", "--name-only", f"{base_branch}...HEAD"])
    if changed is None:
        changed = _run(["git", "diff", "--name-only"])
    return changed or []


def _looks_like_python_web_app(app_py: Path, repo_root: Path) -> bool:
    """Heuristically determine whether app.py is a web entry point.

    Signals used (any one is sufficient):
    - `requirements.txt` contains fastapi/flask/uvicorn/gunicorn.
    - `pyproject.toml` mentions these frameworks in a simple text search.
    - `app.py` itself imports FastAPI/Flask or defines an ASGI app pattern.
    """

    # 1) Check requirements.txt for common web frameworks/servers
    req = repo_root / "requirements.txt"
    if req.exists():
        text = req.read_text().lower()
        if any(name in text for name in ("fastapi", "flask", "uvicorn", "gunicorn")):
            return True

    # 2) Quick scan of pyproject.toml
    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text().lower()
        if any(name in text for name in ("fastapi", "flask", "uvicorn", "gunicorn")):
            return True

    # 3) Inspect app.py content for FastAPI/Flask-like patterns
    try:
        code = app_py.read_text()
    except OSError:
        code = ""

    lowered = code.lower()
    if "fastapi import fastapi" in lowered or "from fastapi" in lowered:
        return True
    if "from flask" in lowered or "flask(" in lowered:
        return True
    if "uvicorn.run" in lowered or "gunicorn" in lowered:
        return True

    return False


def infer_app_type_and_entry(repo_root: Path, changed_files: List[str]) -> tuple[str, Optional[str]]:
    """Heuristic to infer app type and entry point.

    - If `app.py` exists and looks like a web entry (FastAPI/Flask/uvicorn),
      classify as `python-web`.
    - Else if `app.py` exists, treat as `python-cli`.
    - Otherwise, return `unknown`.
    """

    app_py = repo_root / "app.py"
    if app_py.exists():
        if _looks_like_python_web_app(app_py, repo_root):
            return "python-web", "app.py"
        return "python-cli", "app.py"

    # Default fallback if nothing obvious is found.
    return "unknown", None


def observe_repository(repo_root: Path, base_branch: str = "main") -> Observation:
    changed_files = run_git_diff(base_branch, repo_root)
    app_type, entry_point = infer_app_type_and_entry(repo_root, changed_files)
    return Observation(app_type=app_type, entry_point=entry_point, changed_files=changed_files)
