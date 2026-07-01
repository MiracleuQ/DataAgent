from types import SimpleNamespace

import pytest

from app.agents.tool_loop import _parse_content_tool_calls, run_tool_call_loop


def test_parse_dsml_tool_calls_with_typed_parameters():
    content = """
<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="describe_data">
<｜｜DSML｜｜parameter name="columns" string="false">["revenue", "profit"]</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="group_aggregate">
<｜｜DSML｜｜parameter name="group_by" string="true">region</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="agg_col" string="true">revenue</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>
"""

    tool_calls = _parse_content_tool_calls(content)

    assert [call.function.name for call in tool_calls] == ["describe_data", "group_aggregate"]
    assert '"columns": ["revenue", "profit"]' in tool_calls[0].function.arguments
    assert '"group_by": "region"' in tool_calls[1].function.arguments


class DsmlToolLLM:
    def __init__(self):
        self.calls = []

    async def chat(self, messages, temperature=0.2, model=None, tools=None):
        self.calls.append({"messages": messages, "tools": tools})
        if len(self.calls) == 1:
            return SimpleNamespace(
                content=(
                    '<｜｜DSML｜｜tool_calls><｜｜DSML｜｜invoke name="group_aggregate">'
                    '<｜｜DSML｜｜parameter name="group_by" string="true">region</｜｜DSML｜｜parameter>'
                    '<｜｜DSML｜｜parameter name="agg_col" string="true">revenue</｜｜DSML｜｜parameter>'
                    "</｜｜DSML｜｜invoke></｜｜DSML｜｜tool_calls>"
                ),
                tool_calls=None,
            )

        assistant_message = next(message for message in messages if message.get("role") == "assistant")
        assert "DSML" not in assistant_message["content"]
        assert any(message.get("role") == "tool" for message in messages)
        return SimpleNamespace(content="Final answer from executed tool", tool_calls=None)


@pytest.mark.asyncio
async def test_run_tool_call_loop_executes_dsml_content_tool_calls():
    executed = []

    def execute_tool(name, args):
        executed.append((name, args))
        return {"ok": True}

    response, summaries = await run_tool_call_loop(
        DsmlToolLLM(),
        messages=[{"role": "user", "content": "analyze"}],
        tools=[],
        execute_tool=execute_tool,
    )

    assert response.content == "Final answer from executed tool"
    assert executed == [("group_aggregate", {"group_by": "region", "agg_col": "revenue"})]
    assert summaries == ['group_aggregate: {"ok": true}']
