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

    # Monkeypatch docker-related calls so the test doesn't require docker
    monkeypatch.setattr(runner, "build_image", lambda *a, **k: False)
    monkeypatch.setattr(runner, "run_container_and_tests", lambda *a, **k: (False, "", "docker not available"))

    report_path = runner.run_e2e(repo_root, agent_dir, obs, container_plan, test_plan)

    report_text = report_path.read_text()
    assert "Impacted Areas" in report_text
    assert "Pass/Fail Status" in report_text
