import traceback

from app.agents.base import AgentResult, BaseAgent
from app.agents.tool_loop import run_tool_call_loop
from app.core.context import DataContext
from app.core.sandbox import Sandbox
from app.llm.client import LLMClient
from app.tools.analysis_tools import get_analysis_tools
from app.tools.registry import ToolRegistry

SYSTEM_PROMPT = """你是数据分析 Agent。你的职责是：
1. 对数据进行统计分析
2. 根据需求选择合适的分析工具
3. 将分析结果转化为清晰的洞察摘要

可用工具：describe_data, group_aggregate, correlation, detect_anomaly
输出分析结果摘要。"""


class AnalystAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, sandbox_timeout: int = 30):
        registry = ToolRegistry()
        for tool in get_analysis_tools():
            registry.register(tool)
        super().__init__(role="analyst", system_prompt=SYSTEM_PROMPT, tools=registry)
        self._llm = llm_client
        self._sandbox = Sandbox(timeout=sandbox_timeout)

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            full_task = f"{task}\n\n当前数据状态：\n{context.summary()}"
            messages = self._build_messages(full_task)
            openai_tools = self.tools.to_openai_tools()

            def execute_tool(func_name, args):
                df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                if not df_name:
                    raise ValueError("No dataframe is available for analysis")
                df = context.get_dataframe(df_name)
                if df is None:
                    raise ValueError(f"DataFrame '{df_name}' not found")
                result = self.tools.call(func_name, df=df, **args)
                stored = result if not hasattr(result, "to_dict") else result.to_dict()
                context.add_result(f"{func_name}_{df_name}", stored)
                return stored

            response, tool_summaries = await run_tool_call_loop(
                self._llm,
                messages,
                openai_tools,
                execute_tool,
            )
            output = response.content or "\n".join(tool_summaries) or "分析完成"
            self._remember(task, output)
            return AgentResult(success=True, output=output, agent_id=self.role)
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
