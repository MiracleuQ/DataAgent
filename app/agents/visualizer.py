import logging
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent, AgentResult, resolve_dataframe
from app.agents.tool_loop import run_tool_call_loop
from app.core.bus import MessageBus
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.chart_tools import get_chart_tools
from app.tools.registry import ToolRegistry
from app.utils.language import get_prompt

logger = setup_logger(__name__)


class VisualizerAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, chart_output_dir: str = "data/charts", bus: Optional[MessageBus] = None):
        registry = ToolRegistry()
        for tool in get_chart_tools():
            registry.register(tool)
        super().__init__(role="visualizer", system_prompt=get_prompt("visualizer"), tools=registry, bus=bus)
        self._llm = llm_client
        self._chart_dir = chart_output_dir

    def _make_execute_tool(self, context: DataContext, purpose: str = "visualization"):
        charts = []

        def execute_tool(func_name: str, args: Dict[str, Any]) -> Any:
            df_name = args.get("df_name") or (context.list_dataframes()[0] if context.list_dataframes() else None)
            df = resolve_dataframe(context, args, purpose)
            df_columns = list(df.columns)
            for key in ("x", "y", "labels", "values"):
                prefix = f"{df_name}."
                if key in args and isinstance(args[key], str) and args[key].startswith(prefix):
                    args[key] = args[key][len(prefix):]
                if key in args and isinstance(args[key], str) and args[key] not in df_columns:
                    raise ValueError(f"Column '{args[key]}' not found. Available columns: {df_columns}")
            args["output_dir"] = self._chart_dir
            path = self.tools.call(func_name, df=df, **args)
            context.add_chart(path)
            charts.append(path)
            return f"Chart saved to: {path}"

        execute_tool.charts = charts
        return execute_tool

    async def run(self, task: str, context: DataContext) -> AgentResult:
        df_info = context.summary()
        full_task = f"{task}\n\n当前数据状态：\n{df_info}\n图表输出目录：{self._chart_dir}"
        messages = self._build_messages(full_task)
        openai_tools = self.tools.to_openai_tools()
        execute_tool = self._make_execute_tool(context)

        response, tool_summaries = await run_tool_call_loop(
            self._llm, messages, openai_tools, execute_tool,
        )
        charts = getattr(execute_tool, "charts", [])
        output = f"生成 {len(charts)} 个图表：\n" + "\n".join(charts) if charts else (response.content or "未生成图表")
        self._remember(task, output)
        return AgentResult(success=True, output=output, agent_id=self.role, data={"charts": charts})
