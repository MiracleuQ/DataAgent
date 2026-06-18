import logging
from typing import Optional

from app.agents.base import AgentResult, BaseAgent
from app.agents.tool_loop import run_tool_call_loop
from app.core.bus import MessageBus
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.analysis_tools import get_analysis_tools
from app.tools.registry import ToolRegistry
from app.utils.language import get_prompt

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, bus: Optional[MessageBus] = None):
        registry = ToolRegistry()
        for tool in get_analysis_tools():
            registry.register(tool)
        super().__init__(role="reviewer", system_prompt=get_prompt("reviewer"), tools=registry, bus=bus)
        self._llm = llm_client

    async def run(self, task: str, context: DataContext) -> AgentResult:
        final_report = context.get_result("final_report") or ""
        review_task = (
            f"{task}\n\n"
            f"Final report:\n{final_report}\n\n"
            f"Data context:\n{context.summary()}\n\n"
            f"Analysis results:\n{list(context.analysis_results.keys())}\n\n"
            f"Artifacts:\n{context.artifact_summary()}"
        )
        messages = self._build_messages(review_task)
        openai_tools = self.tools.to_openai_tools()
        execute_tool = self._make_execute_tool(context, purpose="review verification")

        response, _tool_summaries = await run_tool_call_loop(
            self._llm, messages, openai_tools, execute_tool,
        )
        output = response.content or "Review could not be generated."
        context.add_result("review_report", output)
        self._remember(task, output)
        return AgentResult(success=True, output=output, agent_id=self.role)
