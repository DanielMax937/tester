from pathlib import Path

from sdet_agent import observe


def test_observation_infers_basic_app_type(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("print('hello')\n")

    def fake_run_git_diff(base, repo_root):  # noqa: ARG001
        return []

    monkeypatch.setattr(observe, "run_git_diff", fake_run_git_diff)

    obs = observe.observe_repository(tmp_path, base_branch="main")

    assert obs.app_type == "python-cli"
    assert obs.entry_point == "app.py"


def test_observation_infers_python_web_from_fastapi(tmp_path, monkeypatch):
    app_code = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"hello": "world"}
"""
    (tmp_path / "app.py").write_text(app_code)
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")

    def fake_run_git_diff(base, repo_root):  # noqa: ARG001
        return []

    monkeypatch.setattr(observe, "run_git_diff", fake_run_git_diff)

    obs = observe.observe_repository(tmp_path, base_branch="main")

    assert obs.app_type == "python-web"
    assert obs.entry_point == "app.py"
