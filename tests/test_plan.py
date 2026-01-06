from pathlib import Path

from sdet_agent.observe import Observation
from sdet_agent import plan


def test_plan_creates_basic_container_and_test_plan(tmp_path):
    obs = Observation(
        app_type="python-cli",
        entry_point="app.py",
        changed_files=["app.py"],
    )

    container_plan, test_plan = plan.create_plans(obs, repo_root=Path(tmp_path))

    assert container_plan.base_image.startswith("python:3.11")
    assert container_plan.cmd == ["python", "app.py"]
    assert test_plan.kind == "cli"
    assert any("app.py" in flow.description for flow in test_plan.flows)


def test_plan_creates_web_container_and_test_plan(tmp_path):
    obs = Observation(
        app_type="python-web",
        entry_point="app.py",
        changed_files=["app.py"],
    )

    container_plan, test_plan = plan.create_plans(obs, repo_root=Path(tmp_path))

    assert container_plan.base_image.startswith("python:3.11")
    # Expect a common web port (e.g. 8000) to be mapped
    assert 8000 in container_plan.ports
    assert container_plan.cmd[0] == "python"
    assert "web" in test_plan.kind
    assert any("http://localhost" in flow.description for flow in test_plan.flows)
