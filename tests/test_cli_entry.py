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


def test_cli_run_prints_report_path(tmp_path, monkeypatch):
    # Minimal repo with app.py
    (tmp_path / "app.py").write_text("print('hello')\n")

    # Monkeypatch heavy operations in runner
    from sdet_agent import runner as runner_mod

    def fake_run_e2e(repo_root, agent_dir, obs, container_plan, test_plan):  # noqa: ARG001
        reports_dir = agent_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        path = reports_dir / "latest.md"
        path.write_text("dummy report")
        return path

    monkeypatch.setattr(runner_mod, "run_e2e", fake_run_e2e)

    repo_root = tmp_path
    result = subprocess.run(
        [sys.executable, "-m", "sdet_agent", "run"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert ".agent/reports/latest.md" in result.stdout
