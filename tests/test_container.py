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
    assert "uv" in content
    assert "CMD [\"python\", \"app.py\"]" in content
