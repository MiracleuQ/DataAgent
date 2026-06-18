import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.agents.base import AgentResult, BaseAgent, resolve_dataframe
from app.agents.tool_loop import run_tool_call_loop
from app.core.bus import MessageBus
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.data_tools import get_data_tools
from app.tools.registry import ToolRegistry
from app.utils.language import get_prompt

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
READABLE_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".parquet"}


def _list_data_files() -> str:
    if not DATA_DIR.exists():
        return "No local data files found."
    files = [
        f.name for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in READABLE_SUFFIXES
    ]
    if not files:
        return "No readable data files in data/ directory."
    return "Available data files: " + ", ".join(sorted(files))


class DataEngineerAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, bus: Optional[MessageBus] = None):
        registry = ToolRegistry()
        for tool in get_data_tools():
            registry.register(tool)
        super().__init__(role="data_engineer", system_prompt=get_prompt("data_engineer"), tools=registry, bus=bus)
        self._llm = llm_client

    def _make_execute_tool(self, context: DataContext, purpose: str = "data loading"):
        def execute_tool(func_name: str, args: Dict[str, Any]) -> Any:
            if func_name == "clean_data":
                df_name = args.get("df_name") or (context.list_dataframes()[0] if context.list_dataframes() else None)
                df = resolve_dataframe(context, args, "cleaning")
                cleaned = self.tools.call(func_name, df=df, **args)
                context.add_dataframe(df_name, cleaned)
                return context.data_profile(df_name)

            result = self.tools.call(func_name, **args)
            if hasattr(result, "to_csv"):
                name = args.get("path", "data").split("/")[-1].split(".")[0]
                context.add_dataframe(name, result)
                return context.data_profile(name)
            return result

        return execute_tool

    async def run(self, task: str, context: DataContext) -> AgentResult:
        file_hint = _list_data_files()
        augmented_task = f"{task}\n\n[Data directory contents]\n{file_hint}"
        messages = self._build_messages(augmented_task)
        openai_tools = self.tools.to_openai_tools()
        execute_tool = self._make_execute_tool(context)

        response, tool_summaries = await run_tool_call_loop(
            self._llm, messages, openai_tools, execute_tool,
        )
        output = response.content or "\n".join(tool_summaries) or context.summary()
        self._remember(task, output)
        return AgentResult(success=True, output=output, agent_id=self.role)
