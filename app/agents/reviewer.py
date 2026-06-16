import logging
from typing import Optional

from app.agents.base import AgentResult, BaseAgent
from app.agents.tool_loop import run_tool_call_loop, _clean_content
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
        try:
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

            def execute_tool(func_name, args):
                df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                if not df_name:
                    raise ValueError("No dataframe available for review verification")
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
            output = _clean_content(response.content) or "Review could not be generated."
            context.add_result("review_report", output)
            self._remember(task, output)
            return AgentResult(success=True, output=output, agent_id=self.role)
        except Exception as e:
            logger.error("ReviewerAgent failed: %s", e, exc_info=True)
            return AgentResult(success=False, output="", agent_id=self.role, error=str(e))
