import os
import pytest
from app.history import HistoryManager

@pytest.fixture
def history(tmp_path):
    db_path = str(tmp_path / "test_history.db")
    return HistoryManager(db_path=db_path)

def test_create_session(history):
    history.create_session("test-1", "分析销售数据")
    session = history.get_session("test-1")
    assert session is not None
    assert session["user_request"] == "分析销售数据"

def test_update_session(history):
    history.create_session("test-2", "测试")
    history.update_session("test-2", '{"tasks": []}', "完成", "success")
    session = history.get_session("test-2")
    assert session["status"] == "success"

def test_log_agent(history):
    history.create_session("test-3", "测试")
    history.log_agent("test-3", "analyst", "分析数据", "分析完成", True)
    logs = history.get_agent_logs("test-3")
    assert len(logs) == 1
    assert logs[0]["agent_name"] == "analyst"

def test_get_sessions(history):
    history.create_session("test-4", "测试1")
    history.create_session("test-5", "测试2")
    sessions = history.get_sessions()
    assert len(sessions) == 2
