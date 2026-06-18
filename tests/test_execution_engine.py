import asyncio
import time
from types import SimpleNamespace

import pytest

from app.agents.base import AgentResult, BaseAgent
from app.agents.coordinator import CoordinatorAgent
from app.core.context import DataContext
from app.core.orchestrator import Orchestrator


class SlowAgent(BaseAgent):
    def __init__(self, role: str, delay: float = 0.2):
        super().__init__(role=role, system_prompt="slow")
        self.delay = delay

    async def run(self, task: str, context: DataContext) -> AgentResult:
        await asyncio.sleep(self.delay)
        return AgentResult(success=True, output=f"{self.role} done", agent_id=self.role)


class PlanLLM:
    async def chat(self, messages, temperature=0.2, model=None, tools=None, response_format=None):
        return SimpleNamespace(
            content='{"understanding": "parallel", "tasks": ['
            '{"agent": "analyst", "task": "a", "depends_on": []},'
            '{"agent": "visualizer", "task": "v", "depends_on": []}'
            "]}",
            tool_calls=None,
        )


@pytest.mark.asyncio
async def test_orchestrator_runs_ready_tasks_concurrently_and_records_events():
    orchestrator = Orchestrator()
    orchestrator.register_agent(SlowAgent("analyst", delay=0.25))
    orchestrator.register_agent(SlowAgent("visualizer", delay=0.25))

    start = time.perf_counter()
    results = await orchestrator.execute_plan(
        {
            "tasks": [
                {"agent": "analyst", "task": "a", "depends_on": []},
                {"agent": "visualizer", "task": "v", "depends_on": []},
            ]
        },
        DataContext(),
    )
    elapsed = time.perf_counter() - start

    assert elapsed < 0.45
    assert results["analyst_0"].success is True
    assert results["visualizer_1"].success is True
    events = orchestrator.execution_events
    assert [event["status"] for event in events].count("running") == 2
    assert [event["status"] for event in events].count("success") == 2
    assert all(event["duration_ms"] >= 0 for event in events if event["status"] == "success")


@pytest.mark.asyncio
async def test_orchestrator_run_returns_execution_summary(tmp_path):
    orchestrator = Orchestrator(history_db_path=str(tmp_path / "history.db"))
    orchestrator.register_agent(SlowAgent("analyst", delay=0.01))
    orchestrator.register_agent(SlowAgent("visualizer", delay=0.01))
    coordinator = CoordinatorAgent(llm_client=PlanLLM())

    result = await orchestrator.run("analyze", DataContext(), coordinator)

    assert result["execution"]["total_tasks"] == 2
    assert result["execution"]["succeeded"] == 2
    assert result["execution"]["failed"] == 0
    assert result["execution"]["duration_ms"] >= 0
    assert len(result["execution"]["events"]) >= 4
