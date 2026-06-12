import json
import traceback
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.chart_tools import get_chart_tools
from app.tools.registry import ToolRegistry

SYSTEM_PROMPT = """你是数据可视化 Agent。你的职责是根据数据分析结果生成合适的图表。

可用图表：plot_line(折线图), plot_bar(柱状图), plot_scatter(散点图), plot_pie(饼图)

选择原则：时间序列→折线图, 分类对比→柱状图, 两变量关系→散点图, 占比→饼图
图表标题使用中文。"""


class VisualizerAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, chart_output_dir: str = "data/charts"):
        registry = ToolRegistry()
        for tool in get_chart_tools():
            registry.register(tool)
        super().__init__(role="visualizer", system_prompt=SYSTEM_PROMPT, tools=registry)
        self._llm = llm_client
        self._chart_dir = chart_output_dir

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            df_info = context.summary()
            full_task = f"{task}\n\n当前数据状态：\n{df_info}\n图表输出目录：{self._chart_dir}"
            messages = self._build_messages(full_task)
            openai_tools = self.tools.to_openai_tools()
            response = await self._llm.chat(messages=messages, tools=openai_tools)

            charts = []
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                    if df_name:
                        df = context.get_dataframe(df_name)
                        if df is not None:
                            args["output_dir"] = self._chart_dir
                            path = self.tools.call(func_name, df=df, **args)
                            context.add_chart(path)
                            charts.append(path)

            output = f"生成 {len(charts)} 个图表：\n" + "\n".join(charts) if charts else "未生成图表"
            self._remember(task, output)
            return AgentResult(success=True, output=output, agent_id=self.role, data={"charts": charts})
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
