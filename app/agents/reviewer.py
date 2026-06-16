import traceback

from app.agents.base import AgentResult, BaseAgent
from app.core.context import DataContext
from app.llm.client import LLMClient

SYSTEM_PROMPT = """你是数据分析审阅 Agent。你的职责是：
1. 检查报告中的结论是否有数据或 artifact 支撑
2. 指出缺失值、异常值、样本量、相关性等可能影响结论的风险
3. 给出简洁的审阅结论和改进建议

不要编造数据。只能基于上下文中已有的数据摘要、分析结果和 artifacts 审阅。"""


class ReviewerAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(role="reviewer", system_prompt=SYSTEM_PROMPT)
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
            response = await self._llm.chat(messages=messages, temperature=0.1)
            output = response.content or "Review could not be generated."
            context.add_result("review_report", output)
            self._remember(task, output)
            return AgentResult(success=True, output=output, agent_id=self.role)
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
