import json
import traceback
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.data_tools import get_data_tools
from app.tools.registry import ToolRegistry

SYSTEM_PROMPT = """你是数据工程师 Agent。你的职责是：
1. 根据用户描述，选择合适的数据源加载数据
2. 对数据进行清洗
3. 将处理好的数据存入共享上下文

可用工具：read_file, read_sql, call_api, parse_text, clean_data

工作流程：分析需求 → 调用工具加载数据 → 清洗数据 → 返回数据概览
只输出数据概览结果。"""


class DataEngineerAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        registry = ToolRegistry()
        for tool in get_data_tools():
            registry.register(tool)
        super().__init__(role="data_engineer", system_prompt=SYSTEM_PROMPT, tools=registry)
        self._llm = llm_client

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            messages = self._build_messages(task)
            openai_tools = self.tools.to_openai_tools()
            response = await self._llm.chat(messages=messages, tools=openai_tools)

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    if func_name == "clean_data":
                        df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                        if df_name:
                            df = context.get_dataframe(df_name)
                            if df is not None:
                                cleaned = self.tools.call(func_name, df=df, **args)
                                context.add_dataframe(df_name, cleaned)
                    else:
                        result = self.tools.call(func_name, **args)
                        if hasattr(result, "to_csv"):
                            name = args.get("path", "data").split("/")[-1].split(".")[0]
                            context.add_dataframe(name, result)

            summary = context.summary()
            self._remember(task, summary)
            return AgentResult(success=True, output=summary, agent_id=self.role)
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
