import asyncio
import pytest
from app.core.context import DataContext
from app.core.bus import MessageBus, Message
from app.core.sandbox import Sandbox
from app.history import HistoryManager


def test_context_operations():
    ctx = DataContext()
    import pandas as pd
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    ctx.add_dataframe("test", df)
    assert "test" in ctx.list_dataframes()
    assert len(ctx.get_dataframe("test")) == 3


def test_bus_operations():
    async def _run():
        bus = MessageBus()
        msg = Message(sender="a", receiver="b", content="test")
        await bus.send(msg)
        messages = await bus.receive("b")
        assert len(messages) == 1

    asyncio.run(_run())


def test_sandbox_safe_execution():
    sandbox = Sandbox(timeout=5)
    result = sandbox.execute("x = 1 + 1")
    assert result["error"] is None
    assert result["variables"]["x"] == 2


def test_sandbox_blocks_dangerous_code():
    sandbox = Sandbox(timeout=5)
    result = sandbox.execute("import os; os.system('dir')")
    assert "Blocked imports" in result["error"]


def test_sandbox_timeout():
    sandbox = Sandbox(timeout=1)
    result = sandbox.execute("while True: pass")
    assert "timed out" in result["error"]


def test_history_full_flow():
    import gc
    import shutil
    import tempfile
    import os
    tmp = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmp, "test.db")
        history = HistoryManager(db_path=db_path)
        history.create_session("s1", "测试请求")
        history.log_agent("s1", "analyst", "分析", "完成", True)
        history.update_session("s1", "{}", "报告", "success")
        session = history.get_session("s1")
        assert session["status"] == "success"
        logs = history.get_agent_logs("s1")
        assert len(logs) == 1
    finally:
        del history
        gc.collect()
        shutil.rmtree(tmp, ignore_errors=True)
