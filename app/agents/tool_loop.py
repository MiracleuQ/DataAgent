import json
from typing import Any, Callable, Dict, List, Tuple


def _tool_call_name(tool_call: Any) -> str:
    return tool_call.function.name


def _tool_call_arguments(tool_call: Any) -> str:
    return tool_call.function.arguments or "{}"


def _serialize_tool_call(tool_call: Any) -> Dict[str, Any]:
    return {
        "id": getattr(tool_call, "id", ""),
        "type": getattr(tool_call, "type", "function"),
        "function": {
            "name": _tool_call_name(tool_call),
            "arguments": _tool_call_arguments(tool_call),
        },
    }


def _tool_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return str(value)


async def run_tool_call_loop(
    llm: Any,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    execute_tool: Callable[[str, Dict[str, Any]], Any],
    temperature: float = 0.2,
) -> Tuple[Any, List[str]]:
    response = await llm.chat(messages=messages, tools=tools, temperature=temperature)
    tool_calls = getattr(response, "tool_calls", None)
    if not tool_calls:
        return response, []

    follow_up_messages: List[Dict[str, Any]] = list(messages)
    follow_up_messages.append(
        {
            "role": "assistant",
            "content": response.content or "",
            "tool_calls": [_serialize_tool_call(tool_call) for tool_call in tool_calls],
        }
    )

    tool_summaries = []
    for tool_call in tool_calls:
        name = _tool_call_name(tool_call)
        args = json.loads(_tool_call_arguments(tool_call))
        result = execute_tool(name, args)
        content = _tool_content(result)
        tool_summaries.append(f"{name}: {content[:1000]}")
        follow_up_messages.append(
            {
                "role": "tool",
                "tool_call_id": getattr(tool_call, "id", ""),
                "content": content[:4000],
            }
        )

    final_response = await llm.chat(messages=follow_up_messages, temperature=temperature)
    return final_response, tool_summaries
