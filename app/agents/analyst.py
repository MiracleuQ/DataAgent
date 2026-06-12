import json
import traceback
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.core.sandbox import Sandbox
from app.llm.client import LLMClient
from app.tools.analysis_tools import get_analysis_tools
from app.tools.registry import ToolRegistry

SYSTEM_PROMPT = """你是数据分析 Agent。你的职责是：
1. 对数据进行统计分析
2. 根据需求生成 Python 分析代码并在沙箱中执行
3. 将分析结果存入共享上下文

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
            df_info = context.summary()
            full_task = f"{task}\n\n当前数据状态：\n{df_info}"
            messages = self._build_messages(full_task)
            openai_tools = self.tools.to_openai_tools()
            response = await self._llm.chat(messages=messages, tools=openai_tools)

            results = []
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                    if df_name:
                        df = context.get_dataframe(df_name)
                        if df is not None:
                            result = self.tools.call(func_name, df=df, **args)
                            context.add_result(f"{func_name}_{df_name}", result if not hasattr(result, 'to_dict') else result.to_dict())
                            results.append(f"{func_name}: {str(result)[:500]}")

            output = "\n".join(results) if results else (response.content or "分析完成")
            self._remember(task, output)
            return AgentResult(success=True, output=output, agent_id=self.role)
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
