import logging
from typing import Optional

from app.agents.base import BaseAgent, AgentResult
from app.agents.tool_loop import run_tool_call_loop
from app.core.bus import MessageBus
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.analysis_tools import get_analysis_tools
from app.tools.registry import ToolRegistry
from app.utils.language import get_prompt

logger = setup_logger(__name__)


class ReporterAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, bus: Optional[MessageBus] = None):
        registry = ToolRegistry()
        for tool in get_analysis_tools():
            registry.register(tool)
        super().__init__(role="reporter", system_prompt=get_prompt("reporter"), tools=registry, bus=bus)
        self._llm = llm_client

    async def run(self, task: str, context: DataContext) -> AgentResult:
        analysis_summary = []
        for key, value in context.analysis_results.items():
            analysis_summary.append(f"【{key}】\n{str(value)[:1000]}")
        chart_info = f"\n已生成 {len(context.charts)} 个图表" if context.charts else ""
        full_task = f"{task}\n\n数据概况：\n{context.summary()}\n\n分析结果：\n{''.join(analysis_summary)}\n{chart_info}"

        messages = self._build_messages(full_task)
        openai_tools = self.tools.to_openai_tools()
        execute_tool = self._make_execute_tool(context, purpose="verification")

        response, _tool_summaries = await run_tool_call_loop(
            self._llm, messages, openai_tools, execute_tool,
        )
        report = response.content or "无法生成报告"
        context.add_result("final_report", report)
        self._remember(task, report)
        return AgentResult(success=True, output=report, agent_id=self.role)
