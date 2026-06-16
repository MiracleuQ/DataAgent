import logging
from typing import Optional

from app.agents.base import BaseAgent, AgentResult
from app.agents.tool_loop import run_tool_call_loop, _clean_content
from app.core.bus import MessageBus
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.analysis_tools import get_analysis_tools
from app.tools.registry import ToolRegistry
from app.utils.language import get_prompt

logger = logging.getLogger(__name__)


class ReporterAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, bus: Optional[MessageBus] = None):
        registry = ToolRegistry()
        for tool in get_analysis_tools():
            registry.register(tool)
        super().__init__(role="reporter", system_prompt=get_prompt("reporter"), tools=registry, bus=bus)
        self._llm = llm_client

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            analysis_summary = []
            for key, value in context.analysis_results.items():
                analysis_summary.append(f"【{key}】\n{str(value)[:1000]}")
            chart_info = f"\n已生成 {len(context.charts)} 个图表" if context.charts else ""
            full_task = f"{task}\n\n数据概况：\n{context.summary()}\n\n分析结果：\n{''.join(analysis_summary)}\n{chart_info}"

            messages = self._build_messages(full_task)
            openai_tools = self.tools.to_openai_tools()

            def execute_tool(func_name, args):
                df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                if not df_name:
                    raise ValueError("No dataframe available for verification")
                df = context.get_dataframe(df_name)
                if df is None:
                    raise ValueError(f"DataFrame '{df_name}' not found")
                result = self.tools.call(func_name, df=df, **args)
                stored = result if not hasattr(result, "to_dict") else result.to_dict()
                return stored

            response, _tool_summaries = await run_tool_call_loop(
                self._llm,
                messages,
                openai_tools,
                execute_tool,
            )
            report = _clean_content(response.content) or "无法生成报告"
            context.add_result("final_report", report)
            self._remember(task, report)
            return AgentResult(success=True, output=report, agent_id=self.role)
        except Exception as e:
            logger.error("ReporterAgent failed: %s", e, exc_info=True)
            return AgentResult(success=False, output="", agent_id=self.role, error=str(e))
