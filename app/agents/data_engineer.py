import traceback

from app.agents.base import AgentResult, BaseAgent
from app.agents.tool_loop import run_tool_call_loop
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.data_tools import get_data_tools
from app.tools.registry import ToolRegistry

SYSTEM_PROMPT = """你是数据工程师 Agent。你的职责是：
1. 根据用户描述选择合适的数据源加载数据
2. 对数据进行清洗
3. 将处理好的数据存入共享上下文

可用工具：read_file, read_sql, call_api, parse_text, clean_data
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

            def execute_tool(func_name, args):
                if func_name == "clean_data":
                    df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                    if not df_name:
                        raise ValueError("No dataframe is available to clean")
                    df = context.get_dataframe(df_name)
                    if df is None:
                        raise ValueError(f"DataFrame '{df_name}' not found")
                    cleaned = self.tools.call(func_name, df=df, **args)
                    context.add_dataframe(df_name, cleaned)
                    return context.data_profile(df_name)

                result = self.tools.call(func_name, **args)
                if hasattr(result, "to_csv"):
                    name = args.get("path", "data").split("/")[-1].split(".")[0]
                    context.add_dataframe(name, result)
                    return context.data_profile(name)
                return result

            response, tool_summaries = await run_tool_call_loop(
                self._llm,
                messages,
                openai_tools,
                execute_tool,
            )
            output = response.content or "\n".join(tool_summaries) or context.summary()
            self._remember(task, output)
            return AgentResult(success=True, output=output, agent_id=self.role)
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
