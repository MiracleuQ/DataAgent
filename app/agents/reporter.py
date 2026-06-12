import traceback
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient

SYSTEM_PROMPT = """你是数据分析报告 Agent。你的职责是将分析结果转化为清晰的中文洞察报告。

报告格式：
## 分析概要
## 关键发现（3-5 个，每个用一句话+数据支撑）
## 详细分析
## 建议（2-3 条可操作建议）

规则：用数据说话，关键数字加粗，语言简洁。"""


class ReporterAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(role="reporter", system_prompt=SYSTEM_PROMPT)
        self._llm = llm_client

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            analysis_summary = []
            for key, value in context.analysis_results.items():
                analysis_summary.append(f"【{key}】\n{str(value)[:1000]}")
            chart_info = f"\n已生成 {len(context.charts)} 个图表" if context.charts else ""
            full_task = f"{task}\n\n数据概况：\n{context.summary()}\n\n分析结果：\n{''.join(analysis_summary)}\n{chart_info}"

            messages = self._build_messages(full_task)
            response = await self._llm.chat(messages=messages, temperature=0.3)
            report = response.content or "无法生成报告"
            context.add_result("final_report", report)
            self._remember(task, report)
            return AgentResult(success=True, output=report, agent_id=self.role)
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
