import asyncio
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.tools.registry import ToolRegistry


class DummyAgent(BaseAgent):
    async def run(self, task: str, context: DataContext) -> AgentResult:
        return AgentResult(success=True, output="done", agent_id=self.role)


def test_agent_creation():
    agent = DummyAgent(role="test", system_prompt="You are test")
    assert agent.role == "test"


def test_agent_run():
    agent = DummyAgent(role="test", system_prompt="You are test")
    ctx = DataContext()
    result = asyncio.get_event_loop().run_until_complete(agent.run("do something", ctx))
    assert result.success is True
    assert result.output == "done"


def test_agent_tools():
    registry = ToolRegistry()
    agent = DummyAgent(role="test", system_prompt="test", tools=registry)
    assert agent.tools is not None
