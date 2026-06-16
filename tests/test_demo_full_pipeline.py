"""
演示测试：完整数据分析管线 — 从数据加载到异常检测的端到端流程。
不依赖真实 LLM，所有 Agent 交互通过 mock 模拟。
"""
import asyncio
import io
import json
import os
import sys
import tempfile
import gc
import shutil

import pandas as pd
import pytest

from app.tools.registry import Tool, ToolRegistry
from app.tools.data_tools import read_file, clean_data, parse_text, read_sql, call_api, _resolve_allowed_path
from app.tools.analysis_tools import describe_data, group_aggregate, correlation, detect_anomaly
from app.tools.chart_tools import plot_line, plot_bar, plot_scatter, plot_pie
from app.tools.export_tools import export_data, export_to_csv, export_to_json, export_to_markdown, export_to_parquet
from app.core.context import DataContext
from app.core.bus import MessageBus, Message
from app.core.sandbox import Sandbox
from app.core.artifacts import Artifact
from app.core.eda import generate_eda_report
from app.history import HistoryManager


# ═══════════════════════════════════════════════════════════════════
# Fixture: 模拟销售数据集
# ═══════════════════════════════════════════════════════════════════
@pytest.fixture
def sales_data():
    """含缺失值和异常值的销售数据"""
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=20, freq="D"),
        "product": ["Widget_A", "Widget_B", "Widget_A", "Widget_C", "Widget_B",
                     "Widget_A", "Widget_B", "Widget_A", "Widget_C", "Widget_B",
                     "Widget_A", "Widget_B", "Widget_A", "Widget_C", "Widget_B",
                     "Widget_A", "Widget_B", "Widget_A", "Widget_C", "Widget_B"],
        "region":   ["East", "West", "East", "North", "West",
                     "East", None,   "East", "North", "West",
                     "East", "West", "East", "North", "West",
                     "East", "West", "East", "North", "West"],
        "amount":   [120, 150, None, 200, 130,
                     110, 160, 140, 210, 145,
                     125, 155, 135, 205, 150,
                     115, 165, 130, 9999, 140],   # ← 9999 是异常值
        "quantity": [10, 12, 11, 15, 13,
                     9,  14, 12, 16, 11,
                     10, 13, 11, 15, 12,
                     9,  14, 10, 16, 14],
    })


# ═══════════════════════════════════════════════════════════════════
# 阶段 1：数据工具 — 文件读取 & 清洗
# ═══════════════════════════════════════════════════════════════════
class TestStage1_DataTools:
    """阶段 1：数据加载与清洗"""

    def test_load_csv_file(self, sales_data):
        """从临时 CSV 文件加载数据"""
        tmp = tempfile.mkdtemp()
        try:
            csv_path = os.path.join(tmp, "sales.csv")
            sales_data.to_csv(csv_path, index=False)
            df = read_file(csv_path, allowed_root=tmp)
            assert len(df) == 20
            assert list(df.columns) == ["date", "product", "region", "amount", "quantity"]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_parse_text_csv(self):
        """从粘贴的纯文本 CSV 解析"""
        text = "name,score\nAlice,85\nBob,92"
        df = parse_text(text)
        assert len(df) == 2
        assert df["name"].tolist() == ["Alice", "Bob"]

    def test_clean_data_fills_missing_with_median(self, sales_data):
        """清洗：缺失值用中位数填充"""
        assert sales_data["amount"].isna().sum() > 0  # 有缺失值
        cleaned = clean_data(sales_data.copy(), fill_na="median")
        assert cleaned["amount"].isna().sum() == 0
        # 中位数约为 145，确认不是 0
        assert cleaned["amount"].min() > 100

    def test_clean_data_drops_duplicates(self):
        """清洗：去重"""
        dup = pd.DataFrame({"x": [1, 1, 2], "y": [3, 3, 4]})
        cleaned = clean_data(dup, drop_duplicates=True)
        assert len(cleaned) == 2

    def test_resolve_path_rejects_outside_root(self):
        """安全检查：拒绝以 .. 越权的路径"""
        with pytest.raises(PermissionError):
            _resolve_allowed_path("../etc/passwd", allowed_root="data")

    def test_sql_rejects_non_select(self):
        """安全检查：拒绝非 SELECT 的 SQL"""
        with pytest.raises(PermissionError):
            from app.tools.data_tools import _validate_read_query
            _validate_read_query("DROP TABLE users")


# ═══════════════════════════════════════════════════════════════════
# 阶段 2：分析工具 — 统计、聚合、相关性、异常检测
# ═══════════════════════════════════════════════════════════════════
class TestStage2_AnalysisTools:
    """阶段 2：统计分析"""

    def test_describe_data(self, sales_data):
        result = describe_data(sales_data)
        assert result["shape"] == [20, 5]
        assert "amount" in result["dtypes"]
        assert result["missing"]["amount"] == 1  # 1 个缺失值

    def test_group_aggregate_sum(self, sales_data):
        result = group_aggregate(sales_data, "product", "quantity", agg_func="sum")
        assert len(result) == 3
        assert result.loc[result["product"] == "Widget_A", "quantity"].values[0] > 0  # 动态验证

    def test_correlation_matrix(self, sales_data):
        corr = correlation(sales_data)
        # amount 和 quantity 正相关
        assert corr.loc["amount", "quantity"] > 0

    def test_detect_anomaly_iqr(self, sales_data):
        """IQR 方法应检测到 amount=9999 异常值"""
        anomalies = detect_anomaly(sales_data, "amount", method="iqr")
        assert len(anomalies) >= 1
        assert 9999 in anomalies["amount"].values

    def test_detect_anomaly_zscore(self, sales_data):
        """Z-Score 方法也应检测到异常值"""
        anomalies = detect_anomaly(sales_data, "amount", method="zscore")
        assert 9999 in anomalies.values


# ═══════════════════════════════════════════════════════════════════
# 阶段 3：图表工具 — 多种图表生成
# ═══════════════════════════════════════════════════════════════════
class TestStage3_ChartTools:
    """阶段 3：图表生成"""

    def test_create_line_chart(self, sales_data):
        with tempfile.TemporaryDirectory() as d:
            result = plot_line(sales_data, x="date", y="amount", title="Amount Over Time", output_dir=d)
            assert result.endswith(".png")
            assert os.path.exists(result)

    def test_create_bar_chart(self, sales_data):
        agg = sales_data.groupby("product")["amount"].sum().reset_index()
        with tempfile.TemporaryDirectory() as d:
            result = plot_bar(agg, x="product", y="amount", title="Sales by Product", output_dir=d)
            assert result.endswith(".png")
            assert os.path.exists(result)

    def test_create_scatter_chart(self, sales_data):
        with tempfile.TemporaryDirectory() as d:
            result = plot_scatter(sales_data, x="quantity", y="amount", title="Qty vs Amount", output_dir=d)
            assert result.endswith(".png")
            assert os.path.exists(result)

    def test_create_pie_chart(self, sales_data):
        agg = sales_data.groupby("region")["amount"].sum().reset_index()
        with tempfile.TemporaryDirectory() as d:
            result = plot_pie(agg, labels="region", values="amount", title="Sales by Region", output_dir=d)
            assert result.endswith(".png")
            assert os.path.exists(result)

    def test_all_chart_types_export(self, sales_data):
        """同一数据集生成全部 4 种图表"""
        charts = []
        with tempfile.TemporaryDirectory() as d:
            charts.append(plot_line(sales_data, x="date", y="amount", title="Line", output_dir=d))
            agg_product = sales_data.groupby("product")["amount"].sum().reset_index()
            charts.append(plot_bar(agg_product, x="product", y="amount", title="Bar", output_dir=d))
            charts.append(plot_scatter(sales_data, x="quantity", y="amount", title="Scatter", output_dir=d))
            agg_region = sales_data.groupby("region")["amount"].sum().reset_index()
            charts.append(plot_pie(agg_region, labels="region", values="amount", title="Pie", output_dir=d))
            for p in charts:
                assert os.path.exists(p)
        assert len(charts) == 4


# ═══════════════════════════════════════════════════════════════════
# 阶段 4：数据导出 — 多种格式
# ═══════════════════════════════════════════════════════════════════
class TestStage4_ExportTools:
    """阶段 4：多格式数据导出"""

    def test_export_to_excel(self, sales_data):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.xlsx")
            result = export_data(format_type="excel", output_path=path, dataframes={"sales": sales_data.copy()})
            assert result == path
            assert os.path.exists(path)

    def test_export_to_csv(self, sales_data):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.csv")
            result = export_to_csv(sales_data.copy(), output_path=path)
            assert result == path
            reimported = pd.read_csv(path)
            assert len(reimported) == 20

    def test_export_to_json(self, sales_data):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.json")
            result = export_to_json(sales_data.to_dict(orient="records"), output_path=path)
            assert result == path
            assert os.path.exists(path)

    def test_export_to_markdown(self, sales_data):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.md")
            result = export_to_markdown(report="# Sales Report\nSummary text", charts=[], output_path=path)
            assert result == path
            content = open(path).read()
            assert "Sales Report" in content

    def test_export_to_parquet(self, sales_data):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.parquet")
            result = export_to_parquet(sales_data.copy(), output_path=path)
            assert result == path
            reimported = pd.read_parquet(path)
            assert len(reimported) == 20


# ═══════════════════════════════════════════════════════════════════
# 阶段 5：DataContext & EDA — 上下文与自动探索性分析
# ═══════════════════════════════════════════════════════════════════
class TestStage5_ContextAndEDA:
    """阶段 5：共享上下文 + 自动 EDA"""

    def test_auto_eda_on_add_dataframe(self, sales_data):
        ctx = DataContext()
        ctx.add_dataframe("sales", sales_data, auto_profile=True)
        assert len(ctx.artifacts) == 1
        artifact = ctx.artifacts[0]
        assert artifact.kind == "eda"
        assert artifact.data["shape"] == {"rows": 20, "columns": 5}
        # 应检测到缺失值 和 异常值
        finding_types = [f["type"] for f in artifact.data["findings"]]
        assert "missing_values" in finding_types
        assert "potential_outliers" in finding_types

    def test_data_profile_includes_statistics(self, sales_data):
        ctx = DataContext()
        ctx.add_dataframe("sales", sales_data)
        profile = ctx.data_profile("sales")
        assert "columns" in profile
        assert "amount" in profile["columns"]
        col_profile = profile["columns"]["amount"]
        assert "min" in col_profile
        assert "max" in col_profile
        assert col_profile["missing_count"] == 1

    def test_context_summary_non_empty(self, sales_data):
        ctx = DataContext()
        ctx.add_dataframe("sales", sales_data)
        ctx.add_result("final_report", "Sales increased by 12%.")
        summary = ctx.summary()
        assert "DataFrame 'sales'" in summary
        assert "Analysis result: final_report" in summary

    def test_artifact_summary(self):
        ctx = DataContext()
        ctx.add_artifact(Artifact(kind="chart", title="Revenue Chart", summary="Bar chart"))
        ctx.add_artifact(Artifact(kind="table", title="Summary Table", summary="Top 5"))
        summary_text = ctx.artifact_summary()
        assert "Revenue Chart" in summary_text
        assert "Summary Table" in summary_text

    def test_get_nonexistent_dataframe_returns_none(self):
        ctx = DataContext()
        assert ctx.get_dataframe("ghost") is None

    def test_get_nonexistent_result_returns_none(self):
        ctx = DataContext()
        assert ctx.get_result("ghost") is None


# ═══════════════════════════════════════════════════════════════════
# 阶段 6：消息总线 — Agent 间通信
# ═══════════════════════════════════════════════════════════════════
class TestStage6_MessageBus:
    """阶段 6：Agent 间消息通信"""

    @pytest.mark.asyncio
    async def test_send_and_receive(self):
        bus = MessageBus()
        await bus.send(Message(sender="analyst", receiver="reporter", content="异常值: 1 条"))
        msgs = await bus.receive("reporter")
        assert len(msgs) == 1
        assert msgs[0].content == "异常值: 1 条"

    @pytest.mark.asyncio
    async def test_receive_clears_inbox(self):
        bus = MessageBus()
        await bus.send(Message(sender="a", receiver="b", content="hi"))
        msgs1 = await bus.receive("b")
        assert len(msgs1) == 1
        msgs2 = await bus.receive("b")  # 第二次应为空
        assert len(msgs2) == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_all_agents(self):
        bus = MessageBus()
        await bus.broadcast("coordinator", "开始分析")
        for agent in ["data_engineer", "analyst", "visualizer", "reporter", "reviewer"]:
            msgs = await bus.receive(agent)
            assert len(msgs) == 1
            assert msgs[0].content == "开始分析"

    @pytest.mark.asyncio
    async def test_request_data_with_subscription(self):
        bus = MessageBus()
        received = []

        async def handler(msg):
            received.append(msg.content)
            await bus.send(Message(
                sender="data_engineer", receiver=msg.sender,
                content=json.dumps({"data": "loaded"}), msg_type="data_response",
                metadata={"request_id": msg.metadata.get("request_id", "")}
            ))

        bus.subscribe("data_engineer", "data_request", handler)
        response = await bus.request_data("analyst", "data_engineer", "加载销售数据")
        assert response is not None
        assert "loaded" in response.content

    @pytest.mark.asyncio
    async def test_get_history_filtered(self):
        bus = MessageBus()
        await bus.send(Message(sender="a", receiver="b", content="msg1", msg_type="task"))
        await bus.send(Message(sender="b", receiver="c", content="msg2", msg_type="error"))
        history_a = await bus.get_history(agent_id="a")
        assert len(history_a) == 1
        history_b = await bus.get_history(agent_id="b")
        assert len(history_b) == 2


# ═══════════════════════════════════════════════════════════════════
# 阶段 7：安全沙箱 — 代码隔离执行
# ═══════════════════════════════════════════════════════════════════
class TestStage7_Sandbox:
    """阶段 7：安全沙箱"""

    @pytest.mark.skipif(sys.platform == "win32" and sys.version_info >= (3, 13),
                        reason="Python 3.13+ Windows spawn incompatible with SimpleNamespace")
    def test_execute_arithmetic(self):
        sandbox = Sandbox(timeout=5)
        result = sandbox.execute("a = sum([1, 2, 3])\nb = a * 2")
        assert result["error"] is None
        assert result["variables"]["a"] == 6
        assert result["variables"]["b"] == 12

    @pytest.mark.skipif(sys.platform == "win32" and sys.version_info >= (3, 13),
                        reason="Python 3.13+ Windows spawn incompatible with SimpleNamespace")
    def test_execute_numpy(self):
        sandbox = Sandbox(timeout=5)
        result = sandbox.execute("import numpy as np\nmean = np.mean([1,2,3,4,5])")
        assert result["error"] is None
        assert result["variables"]["mean"] == 3.0

    def test_block_os_import(self):
        sandbox = Sandbox(timeout=5)
        result = sandbox.execute("import os\nx = os.getcwd()")
        assert "Blocked imports" in result["error"]

    def test_block_subprocess(self):
        sandbox = Sandbox(timeout=5)
        result = sandbox.execute("import subprocess\nsubprocess.run('dir')")
        assert "Blocked imports" in result["error"]

    def test_timeout_infinite_loop(self):
        sandbox = Sandbox(timeout=1)
        result = sandbox.execute("while True:\n    pass")
        assert "timed out" in result["error"]


# ═══════════════════════════════════════════════════════════════════
# 阶段 8：工具注册表 — 完整注册与调用
# ═══════════════════════════════════════════════════════════════════
class TestStage8_ToolRegistry:
    """阶段 8：工具注册表全功能"""

    def test_register_all_data_tools(self):
        from app.tools.data_tools import get_data_tools
        reg = ToolRegistry()
        for tool in get_data_tools():
            reg.register(tool)
        names = [t.name for t in reg.list_tools()]
        assert "read_file" in names
        assert "clean_data" in names
        assert "export_data" in names

    def test_register_all_analysis_tools(self):
        from app.tools.analysis_tools import get_analysis_tools
        reg = ToolRegistry()
        for tool in get_analysis_tools():
            reg.register(tool)
        names = [t.name for t in reg.list_tools()]
        assert "describe_data" in names
        assert "detect_anomaly" in names
        assert "correlation" in names

    def test_call_tool_through_registry(self):
        reg = ToolRegistry()
        reg.register(Tool(name="double", description="Double a number",
                          parameters={"type": "object", "properties": {"n": {"type": "integer"}}},
                          function=lambda n: n * 2))
        result = reg.call("double", n=21)
        assert result == 42

    def test_call_nonexistent_tool_raises(self):
        reg = ToolRegistry()
        with pytest.raises(ValueError, match="not found"):
            reg.call("ghost_tool")

    def test_cache_invalidation_on_register(self):
        reg = ToolRegistry()
        reg.register(Tool(name="t1", description="d1", parameters={}, function=lambda: 1))
        tools1 = reg.to_openai_tools()
        reg.register(Tool(name="t2", description="d2", parameters={}, function=lambda: 2))
        tools2 = reg.to_openai_tools()
        assert len(tools1) == 1
        assert len(tools2) == 2  # 缓存已失效，重新生成


# ═══════════════════════════════════════════════════════════════════
# 阶段 9：历史记录 — 完整会话流程
# ═══════════════════════════════════════════════════════════════════
class TestStage9_History:
    """阶段 9：历史记录持久化"""

    def test_full_session_lifecycle(self):
        tmp = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmp, "hist.db")
            history = HistoryManager(db_path=db_path)

            history.create_session("S001", "分析销售数据趋势")
            history.log_agent("S001", "data_engineer", "加载", "成功加载20行", True)
            history.log_agent("S001", "analyst", "分析", "发现1个异常值", True)
            history.log_agent("S001", "reporter", "报告", "销售额增长12%", True)
            history.update_session("S001", plan='{"tasks":[]}', result="报告完成", status="success")

            session = history.get_session("S001")
            assert session["user_request"] == "分析销售数据趋势"
            assert session["status"] == "success"

            logs = history.get_agent_logs("S001")
            assert len(logs) == 3
            assert logs[0]["agent_name"] == "data_engineer"

            sessions = history.get_sessions()
            assert len(sessions) >= 1
        finally:
            del history
            gc.collect()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_multiple_sessions(self):
        tmp = tempfile.mkdtemp()
        try:
            db_path = os.path.join(tmp, "hist2.db")
            history = HistoryManager(db_path=db_path)
            history.create_session("A", "请求A")
            history.create_session("B", "请求B")
            history.create_session("C", "请求C")
            sessions = history.get_sessions()
            assert len(sessions) == 3
        finally:
            del history
            gc.collect()
            shutil.rmtree(tmp, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════
# 阶段 10：端到端编排 — 模拟完整 Agent 协作链路
# ═══════════════════════════════════════════════════════════════════
class TestStage10_EndToEndOrchestration:
    """阶段 10：端到端编排（不依赖 LLM）"""

    def test_orchestrator_runs_all_tasks_in_order(self):
        """
        模拟 6 Agent 协作：
        Coordinator → DataEngineer → Analyst → Visualizer → Reporter → Reviewer
        """
        from app.agents.base import BaseAgent, AgentResult
        from app.core.orchestrator import Orchestrator

        class MockAgent(BaseAgent):
            def __init__(self, role, output_text):
                super().__init__(role=role, system_prompt=f"You are {role}")
                self.output_text = output_text

            async def run(self, task, context):
                return AgentResult(success=True, output=self.output_text, agent_id=self.role)

        orch = Orchestrator(history_db_path=":memory:")
        orch.register_agent(MockAgent("data_engineer", "Data loaded"))
        orch.register_agent(MockAgent("analyst", "Analysis done"))
        orch.register_agent(MockAgent("visualizer", "Charts generated"))
        orch.register_agent(MockAgent("reporter", "Report written"))
        orch.register_agent(MockAgent("reviewer", "Review passed"))

        plan = {
            "tasks": [
                {"agent": "data_engineer", "task": "加载并清洗数据", "depends_on": []},
                {"agent": "analyst", "task": "统计分析", "depends_on": [0]},
                {"agent": "visualizer", "task": "生成图表", "depends_on": [1]},
                {"agent": "reporter", "task": "撰写报告", "depends_on": [1, 2]},
                {"agent": "reviewer", "task": "审阅报告", "depends_on": [3]},
            ]
        }

        ctx = DataContext()
        results = asyncio.run(orch.execute_plan(plan, ctx))

        assert len(results) == 5
        assert results["data_engineer_0"].success
        assert results["analyst_1"].success
        assert results["visualizer_2"].success
        assert results["reporter_3"].success
        assert results["reviewer_4"].success

        # 验证事件记录
        events = orch.execution_events
        assert len(events) == 10  # 5 tasks × 2 events each (running + success)

    def test_orchestrator_skips_dependent_tasks_on_failure(self):
        """依赖失败时自动跳过下游任务"""
        from app.agents.base import BaseAgent, AgentResult
        from app.core.orchestrator import Orchestrator

        class FailingAgent(BaseAgent):
            async def run(self, task, context):
                if self.role == "data_engineer":
                    return AgentResult(success=False, output="", agent_id=self.role, error="File not found")

                return AgentResult(success=True, output="ok", agent_id=self.role)

        orch = Orchestrator(history_db_path=":memory:")
        orch.register_agent(FailingAgent(role="data_engineer", system_prompt=""))
        orch.register_agent(FailingAgent(role="analyst", system_prompt=""))
        orch.register_agent(FailingAgent(role="reporter", system_prompt=""))

        plan = {
            "tasks": [
                {"agent": "data_engineer", "task": "加载数据", "depends_on": []},
                {"agent": "analyst", "task": "分析", "depends_on": [0]},
                {"agent": "reporter", "task": "报告", "depends_on": [1]},
            ]
        }

        ctx = DataContext()
        results = asyncio.run(orch.execute_plan(plan, ctx))

        assert results["data_engineer_0"].success is False
        assert results["analyst_1"].success is False
        assert results["reporter_2"].success is False

        # 验证跳过原因
        assert "failed" in results["analyst_1"].error
        assert "failed" in results["reporter_2"].error

    def test_orchestrator_parallel_execution(self):
        """无依赖的任务应并行执行"""
        from app.agents.base import BaseAgent, AgentResult
        from app.core.orchestrator import Orchestrator
        import time

        class DelayedAgent(BaseAgent):
            async def run(self, task, context):
                await asyncio.sleep(0.2)
                return AgentResult(success=True, output="ok", agent_id=self.role)

        orch = Orchestrator(history_db_path=":memory:")
        orch.register_agent(DelayedAgent(role="analyst", system_prompt=""))
        orch.register_agent(DelayedAgent(role="visualizer", system_prompt=""))

        plan = {
            "tasks": [
                {"agent": "analyst", "task": "分析", "depends_on": []},
                {"agent": "visualizer", "task": "图表", "depends_on": []},
            ]
        }

        ctx = DataContext()
        start = time.perf_counter()
        results = asyncio.run(orch.execute_plan(plan, ctx))
        elapsed = time.perf_counter() - start

        assert len(results) == 2
        assert results["analyst_0"].success
        assert results["visualizer_1"].success
        # 并行执行应远小于串行时间 (0.2×2=0.4s)
        assert elapsed < 0.4

    def test_context_persistence_across_tasks(self):
        """多个 Agent 可以读写同一个 DataContext"""
        from app.agents.base import BaseAgent, AgentResult
        from app.core.orchestrator import Orchestrator

        class ContextAgent(BaseAgent):
            async def run(self, task, context):
                if self.role == "data_engineer":
                    context.add_dataframe("test", pd.DataFrame({"x": [1, 2, 3]}))
                elif self.role == "analyst":
                    df = context.get_dataframe("test")
                    context.add_result("analysis", f"rows={len(df)}")
                return AgentResult(success=True, output=task, agent_id=self.role)

        orch = Orchestrator(history_db_path=":memory:")
        orch.register_agent(ContextAgent(role="data_engineer", system_prompt=""))
        orch.register_agent(ContextAgent(role="analyst", system_prompt=""))

        plan = {
            "tasks": [
                {"agent": "data_engineer", "task": "加载", "depends_on": []},
                {"agent": "analyst", "task": "分析", "depends_on": [0]},
            ]
        }

        ctx = DataContext()
        results = asyncio.run(orch.execute_plan(plan, ctx))

        assert results["analyst_1"].success
        assert ctx.get_result("analysis") == "rows=3"
