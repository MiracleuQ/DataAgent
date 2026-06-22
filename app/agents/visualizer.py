import logging
import json
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent, AgentResult, resolve_dataframe
from app.agents.tool_loop import run_tool_call_loop
from app.core.bus import MessageBus
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.smart_chart_tools import analyze_data_for_chart, create_smart_chart
from app.tools.registry import ToolRegistry
from app.utils.language import get_prompt

logger = logging.getLogger(__name__)


class VisualizerAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, chart_output_dir: str = "data/charts", bus: Optional[MessageBus] = None):
        registry = ToolRegistry()
        for tool in self._get_ai_chart_tools():
            registry.register(tool)
        super().__init__(role="visualizer", system_prompt=get_prompt("visualizer"), tools=registry, bus=bus)
        self._llm = llm_client
        self._chart_dir = chart_output_dir

    def _get_ai_chart_tools(self):
        """获取 AI 图表工具"""
        from app.tools.registry import Tool

        def analyze(df_name: str, context: DataContext = None) -> str:
            if context:
                df = resolve_dataframe(context, {"df_name": df_name}, "analysis")
            else:
                return json.dumps({"error": "No context provided"})
            analysis = analyze_data_for_chart(df, df_name)
            return json.dumps(analysis, ensure_ascii=False)

        def create_chart(df_name: str, chart_type: str, config: Dict[str, Any], context: DataContext = None) -> str:
            if context:
                df = resolve_dataframe(context, {"df_name": df_name}, "visualization")
            else:
                return json.dumps({"error": "No context provided"})
            path = create_smart_chart(df, chart_type, config, df_name, self._chart_dir)
            return f"Chart saved to: {path}"

        return [
            Tool(
                name="analyze_data",
                description="Analyze data features (columns, types, statistics) to recommend chart types. Call this first to understand the data structure.",
                parameters={"type": "object", "properties": {"df_name": {"type": "string"}}, "required": ["df_name"]},
                function=analyze
            ),
            Tool(
                name="create_smart_chart",
                description="Create a beautiful, professional chart using Plotly. Supported types: bar, line, scatter, pie, heatmap, box, histogram, treemap. Config includes: title, x, y, color, etc.",
                parameters={"type": "object", "properties": {
                    "df_name": {"type": "string"},
                    "chart_type": {"type": "string", "enum": ["bar", "line", "scatter", "pie", "heatmap", "box", "histogram", "treemap"]},
                    "config": {"type": "object", "description": "Chart configuration: title, x/y column names, color, size, orientation, etc."}
                }, "required": ["df_name", "chart_type", "config"]},
                function=create_chart
            ),
        ]

    def _make_execute_tool(self, context: DataContext, purpose: str = "visualization"):
        charts = []

        def execute_tool(func_name: str, args: Dict[str, Any]) -> Any:
            if func_name == "analyze_data":
                df_name = args.get("df_name")
                df = resolve_dataframe(context, {"df_name": df_name}, purpose)
                analysis = analyze_data_for_chart(df, df_name)
                return json.dumps(analysis, ensure_ascii=False)

            if func_name == "create_smart_chart":
                df_name = args.get("df_name")
                chart_type = args.get("chart_type")
                config = args.get("config", {})
                df = resolve_dataframe(context, {"df_name": df_name}, purpose)
                path = create_smart_chart(df, chart_type, config, df_name, self._chart_dir)
                context.add_chart(path)
                charts.append(path)
                return f"Chart saved to: {path}"

            df = resolve_dataframe(context, args, purpose)
            path = self.tools.call(func_name, df=df, **args)
            context.add_chart(path)
            charts.append(path)
            return f"Chart saved to: {path}"

        execute_tool.charts = charts
        return execute_tool

    async def run(self, task: str, context: DataContext) -> AgentResult:
        df_info = context.summary()
        full_task = f"""你是一个专业的数据可视化专家。请根据以下数据生成美观、专业的图表。

数据状态：
{df_info}

图表输出目录：{self._chart_dir}

工作流程：
1. 首先使用 analyze_data 工具分析数据结构和特征
2. 根据分析结果，选择最合适的图表类型
3. 使用 create_smart_chart 工具创建图表

图表类型选择指南：
- bar: 适合分类数据对比
- line: 适合时间序列或趋势分析
- scatter: 适合展示两个变量的关系
- pie: 适合展示占比关系（类别不超过7个）
- heatmap: 适合展示相关性矩阵
- box: 适合展示数据分布和异常值
- histogram: 适合展示数据分布
- treemap: 适合展示层级结构

请生成至少2-3个不同类型的图表来全面展示数据。每个图表都要有清晰的标题和标签。"""
        messages = self._build_messages(full_task)
        openai_tools = self.tools.to_openai_tools()
        execute_tool = self._make_execute_tool(context)

        response, tool_summaries = await run_tool_call_loop(
            self._llm, messages, openai_tools, execute_tool,
        )
        charts = getattr(execute_tool, "charts", [])
        output = f"生成 {len(charts)} 个图表：\n" + "\n".join(charts) if charts else (response.content or "未生成图表")
        self._remember(task, output)
        return AgentResult(success=True, output=output, agent_id=self.role, data={"charts": charts})
