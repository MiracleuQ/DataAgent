from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable[..., Any]


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._openai_tools_cache: Optional[List[Dict[str, Any]]] = None

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
        self._openai_tools_cache = None

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        if self._openai_tools_cache is not None:
            return self._openai_tools_cache
        self._openai_tools_cache = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]
        return self._openai_tools_cache

    def call(self, name: str, **kwargs: Any) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return tool.function(**kwargs)
