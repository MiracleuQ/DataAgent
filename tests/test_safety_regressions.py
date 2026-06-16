import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from app.core.context import DataContext
from app.core.orchestrator import Orchestrator
from app.agents.base import BaseAgent, AgentResult
from app.tools.data_tools import call_api, read_file, read_sql


def test_sandbox_timeout_returns_promptly_for_infinite_loop():
    script = (
        "from app.core.sandbox import Sandbox\n"
        "import time\n"
        "start = time.time()\n"
        "result = Sandbox(timeout=1).execute('while True: pass')\n"
        "elapsed = time.time() - start\n"
        "assert result['error'] == 'Execution timed out after 1 seconds'\n"
        "assert elapsed < 3, elapsed\n"
    )

    proc = subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=2)
        pytest.fail(f"sandbox execution did not return before subprocess timeout\nstdout={stdout}\nstderr={stderr}")

    assert proc.returncode == 0, stderr or stdout


class FailingAgent(BaseAgent):
    async def run(self, task: str, context: DataContext) -> AgentResult:
        return AgentResult(success=False, output="", agent_id=self.role, error="boom")


class RecordingAgent(BaseAgent):
    def __init__(self, role: str):
        super().__init__(role=role, system_prompt="record")
        self.called = False

    async def run(self, task: str, context: DataContext) -> AgentResult:
        self.called = True
        return AgentResult(success=True, output="ran", agent_id=self.role)


@pytest.mark.asyncio
async def test_orchestrator_skips_tasks_when_dependency_fails():
    orchestrator = Orchestrator()
    orchestrator.register_agent(FailingAgent(role="data_engineer", system_prompt="fail"))
    downstream = RecordingAgent(role="analyst")
    orchestrator.register_agent(downstream)

    results = await orchestrator.execute_plan(
        {
            "tasks": [
                {"agent": "data_engineer", "task": "load", "depends_on": []},
                {"agent": "analyst", "task": "analyze", "depends_on": [0]},
            ]
        },
        DataContext(),
    )

    assert results["data_engineer_0"].success is False
    assert results["analyst_1"].success is False
    assert "dependency" in results["analyst_1"].error.lower()
    assert downstream.called is False


def test_orchestrator_accepts_configured_history_db_path(tmp_path):
    db_path = tmp_path / "custom-history.db"

    orchestrator = Orchestrator(history_db_path=str(db_path))

    assert orchestrator._history._db_path == str(db_path)
    assert db_path.exists()


def test_read_file_rejects_paths_outside_allowed_data_root(tmp_path):
    outside = tmp_path / "outside.csv"
    pd.DataFrame({"secret": [1]}).to_csv(outside, index=False)

    with pytest.raises(PermissionError):
        read_file(str(outside))


def test_call_api_rejects_local_network_targets():
    with pytest.raises(PermissionError):
        call_api("http://127.0.0.1:8000/data")


def test_read_sql_rejects_non_select_statements():
    with pytest.raises(PermissionError):
        read_sql("sqlite:///:memory:", "DROP TABLE users")
