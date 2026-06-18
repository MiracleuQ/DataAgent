import asyncio
import json
import re
from typing import Any, Callable, Dict, List, Tuple

_STRIP_XML_RE = re.compile(r"<\s*/?\s*function_?calls\s*>", re.IGNORECASE)
_STRIP_XML_RE2 = re.compile(r"<\s*invoke\s[^>]*>.*?</\s*invoke\s*>", re.DOTALL | re.IGNORECASE)
_STRIP_XML_RE3 = re.compile(r"<\s*parameter\s[^>]*>.*?</\s*parameter\s*>", re.DOTALL | re.IGNORECASE)


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


def _execute_single_tool(tool_call: Any, execute_tool: Callable[[str, Dict[str, Any]], Any]) -> Tuple[str, str, str]:
    name = _tool_call_name(tool_call)
    args = json.loads(_tool_call_arguments(tool_call))
    result = execute_tool(name, args)
    content = _tool_content(result)
    tool_call_id = getattr(tool_call, "id", "")
    return name, content, tool_call_id


def _clean_content(text: str) -> str:
    if not text:
        return ""
    text = _STRIP_XML_RE.sub("", text)
    text = _STRIP_XML_RE2.sub("", text)
    text = _STRIP_XML_RE3.sub("", text)
    return text.strip()


_INVOKE_BLOCK_RE = re.compile(
    r"<\s*invoke\s+name\s*=\s*[\"'](\w+)[\"']\s*>(.*?)<\s*/\s*invoke\s*>",
    re.DOTALL | re.IGNORECASE,
)
_PARAM_RE = re.compile(
    r"<\s*parameter\s+name\s*=\s*[\"'](\w+)[\"'](?:[^>]*?)>\s*(.*?)\s*<\s*/\s*parameter\s*>",
    re.DOTALL | re.IGNORECASE,
)


class _FakeToolCall:
    """Minimal stand-in for an OpenAI tool_call object to reuse _execute_single_tool."""
    def __init__(self, name: str, arguments: Dict[str, Any], call_id: str):
        self._call_id = call_id
        self.function = _FakeFunction(name, arguments)

    @property
    def id(self) -> str:
        return self._call_id

    @property
    def type(self) -> str:
        return "function"


class _FakeFunction:
    def __init__(self, name: str, arguments: Dict[str, Any]):
        self.name = name
        self.arguments = json.dumps(arguments, ensure_ascii=False)


def _parse_content_tool_calls(content: str) -> List[_FakeToolCall]:
    """Extract DeepSeek-style XML function calls from content text."""
    tool_calls = []
    for idx, match in enumerate(_INVOKE_BLOCK_RE.finditer(content)):
        func_name = match.group(1)
        params_block = match.group(2)
        args = {}
        for pm in _PARAM_RE.finditer(params_block):
            args[pm.group(1)] = pm.group(2).strip()
        tool_calls.append(_FakeToolCall(func_name, args, f"content_call_{idx}"))
    return tool_calls


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
        content_tool_calls = _parse_content_tool_calls(response.content or "")
        if not content_tool_calls:
            if hasattr(response, "content") and isinstance(response.content, str):
                response.content = _clean_content(response.content)
            return response, []
        tool_calls = content_tool_calls

    follow_up_messages: List[Dict[str, Any]] = list(messages)
    follow_up_messages.append(
        {
            "role": "assistant",
            "content": response.content or "",
            "tool_calls": [_serialize_tool_call(tool_call) for tool_call in tool_calls],
        }
    )

    MAX_TOOL_CONTENT = 32000
    tool_summaries = []

    for tool_call in tool_calls:
        name = _tool_call_name(tool_call)
        args = json.loads(_tool_call_arguments(tool_call))
        try:
            result = execute_tool(name, args)
            content = _tool_content(result)
        except Exception as e:
            content = f"Error: {e}"
        tool_summaries.append(f"{name}: {content[:1000]}")
        truncated = content[:MAX_TOOL_CONTENT]
        if len(content) > MAX_TOOL_CONTENT:
            truncated += f"\n\n[结果已截断，原长度 {len(content)} 字符，截断至 {MAX_TOOL_CONTENT} 字符]"
        follow_up_messages.append(
            {
                "role": "tool",
                "tool_call_id": getattr(tool_call, "id", ""),
                "content": truncated,
            }
        )

    final_response = await llm.chat(messages=follow_up_messages, temperature=temperature)
    if hasattr(final_response, "content") and isinstance(final_response.content, str):
        final_response.content = _clean_content(final_response.content)
    return final_response, tool_summaries
