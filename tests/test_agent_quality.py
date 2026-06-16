from types import SimpleNamespace

import pandas as pd
import pytest

from app.agents.analyst import AnalystAgent
from app.agents.coordinator import CoordinatorAgent
from app.agents.data_engineer import DataEngineerAgent
from app.core.context import DataContext


class StaticLLM:
    async def chat(self, messages, temperature=0.2, model=None, tools=None):
        return SimpleNamespace(content='{"understanding": "bad", "tasks": [{"agent": "hacker", "task": "x", "depends_on": []}]}', tool_calls=None)


class ToolLoopLLM:
    def __init__(self, tool_name="describe_data", arguments="{}"):
        self.calls = []
        self.tool_name = tool_name
        self.arguments = arguments

    async def chat(self, messages, temperature=0.2, model=None, tools=None):
        self.calls.append({"messages": messages, "tools": tools})
        if len(self.calls) == 1:
            return SimpleNamespace(
                content=None,
                tool_calls=[
                    SimpleNamespace(
                        id="call_1",
                        type="function",
                        function=SimpleNamespace(name=self.tool_name, arguments=self.arguments),
                    )
                ],
            )
        assert any(message.get("role") == "tool" for message in messages)
        return SimpleNamespace(content="Final insight from tool result", tool_calls=None)


def test_coordinator_falls_back_when_plan_uses_unknown_agent():
    coordinator = CoordinatorAgent(llm_client=StaticLLM())

    plan = coordinator._parse_json_response(
        '{"understanding": "bad", "tasks": [{"agent": "hacker", "task": "x", "depends_on": []}]}',
        "analyze sales",
    )

    assert plan["tasks"][0]["agent"] == "data_engineer"
    assert {task["agent"] for task in plan["tasks"]} == {"data_engineer", "analyst", "visualizer", "reporter"}


def test_coordinator_falls_back_when_plan_has_dependency_cycle():
    coordinator = CoordinatorAgent(llm_client=StaticLLM())

    plan = coordinator._parse_json_response(
        '{"understanding": "cycle", "tasks": ['
        '{"agent": "analyst", "task": "a", "depends_on": [1]},'
        '{"agent": "reporter", "task": "b", "depends_on": [0]}'
        "]}",
        "analyze sales",
    )

    assert plan["tasks"][0]["depends_on"] == []
    assert plan["tasks"][-1]["agent"] == "reporter"


def test_context_profile_includes_schema_missing_ranges_and_examples():
    context = DataContext()
    context.add_dataframe(
        "sales",
        pd.DataFrame(
            {
                "region": ["east", "west", "east", None],
                "amount": [10.0, 20.0, None, 40.0],
                "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]),
            }
        ),
    )

    profile = context.data_profile("sales")

    assert profile["name"] == "sales"
    assert profile["shape"] == {"rows": 4, "columns": 3}
    assert profile["columns"]["amount"]["dtype"] == "float64"
    assert profile["columns"]["amount"]["missing_count"] == 1
    assert profile["columns"]["amount"]["min"] == 10.0
    assert profile["columns"]["amount"]["max"] == 40.0
    assert profile["columns"]["region"]["top_values"]["east"] == 2
    assert profile["sample_rows"][0]["region"] == "east"


@pytest.mark.asyncio
async def test_analyst_sends_tool_results_back_to_llm_for_final_summary():
    llm = ToolLoopLLM()
    agent = AnalystAgent(llm_client=llm)
    context = DataContext()
    context.add_dataframe("sales", pd.DataFrame({"amount": [1, 2, 3]}))

    result = await agent.run("describe the data", context)

    assert result.success is True
    assert result.output == "Final insight from tool result"
    assert len(llm.calls) == 2
    assert any(message.get("role") == "tool" for message in llm.calls[1]["messages"])
    assert "describe_data_sales" in context.analysis_results


@pytest.mark.asyncio
async def test_data_engineer_sends_tool_results_back_to_llm_for_final_summary():
    llm = ToolLoopLLM(tool_name="clean_data", arguments='{"fill_na": "zero"}')
    agent = DataEngineerAgent(llm_client=llm)
    context = DataContext()
    context.add_dataframe("sales", pd.DataFrame({"amount": [1.0, None, 3.0]}))

    result = await agent.run("clean sales", context)

    assert result.success is True
    assert result.output == "Final insight from tool result"
    assert len(llm.calls) == 2
    assert context.get_dataframe("sales")["amount"].isna().sum() == 0
