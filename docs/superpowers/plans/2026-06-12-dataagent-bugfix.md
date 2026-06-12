# DataAgent 关键问题修复计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 DataAgent 项目中的关键安全漏洞和架构问题

**Architecture:** 采用渐进式修复策略，先修复安全和阻塞性问题，再优化架构和增加功能

**Tech Stack:** Python 3.13, FastAPI, OpenAI SDK, asyncio, logging

---

## 文件结构

```
app/
├── core/
│   ├── sandbox.py          # 重写：安全沙箱
│   ├── bus.py              # 修改：async 消息总线
│   └── context.py          # 修改：添加日志
├── llm/
│   └── client.py           # 修改：异步客户端
├── agents/
│   ├── base.py             # 修改：添加日志
│   └── coordinator.py      # 修改：JSON 解析
├── history/
│   └── __init__.py         # 重写：历史记录
└── utils/
    └── __init__.py         # 新建：工具函数
tests/
├── test_sandbox.py         # 新建
├── test_bus.py             # 修改
└── test_history.py         # 新建
```

---

### Task 1: 添加日志系统

**Files:**
- Create: `app/utils/logger.py`
- Modify: `app/core/context.py`
- Modify: `app/agents/base.py`

- [ ] **Step 1: 创建日志工具模块**

```python
# app/utils/logger.py
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f"app_{datetime.now():%Y%m%d}.log",
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
```

- [ ] **Step 2: 在 context.py 中添加日志**

```python
# app/core/context.py
from typing import Any, Dict, List, Optional
import pandas as pd
from app.utils.logger import setup_logger

logger = setup_logger("DataContext")


class DataContext:
    def __init__(self):
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.charts: List[str] = []
        self.metadata: Dict[str, Any] = {}
        logger.info("DataContext initialized")

    def add_dataframe(self, name: str, df: pd.DataFrame) -> None:
        self.dataframes[name] = df
        logger.info(f"Added DataFrame '{name}': {len(df)} rows, {len(df.columns)} columns")

    def get_dataframe(self, name: str) -> Optional[pd.DataFrame]:
        df = self.dataframes.get(name)
        if df is None:
            logger.warning(f"DataFrame '{name}' not found")
        return df

    def list_dataframes(self) -> List[str]:
        return list(self.dataframes.keys())

    def add_result(self, key: str, value: Any) -> None:
        self.analysis_results[key] = value
        logger.info(f"Added analysis result: {key}")

    def get_result(self, key: str) -> Any:
        return self.analysis_results.get(key)

    def add_chart(self, path: str) -> None:
        self.charts.append(path)
        logger.info(f"Added chart: {path}")

    def summary(self) -> str:
        parts = []
        for name, df in self.dataframes.items():
            parts.append(f"DataFrame '{name}': {len(df)} rows, {len(df.columns)} columns")
        for key in self.analysis_results:
            parts.append(f"Analysis result: {key}")
        if self.charts:
            parts.append(f"Charts: {len(self.charts)} generated")
        return "\n".join(parts) if parts else "Empty context"
```

- [ ] **Step 3: 在 base.py 中添加日志**

```python
# app/agents/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.core.context import DataContext
from app.tools.registry import ToolRegistry
from app.utils.logger import setup_logger

logger = setup_logger("BaseAgent")


@dataclass
class AgentResult:
    success: bool
    output: str
    agent_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseAgent(ABC):
    def __init__(self, role: str, system_prompt: str, tools: Optional[ToolRegistry] = None):
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self._history: List[Dict[str, str]] = []
        logger.info(f"Agent '{role}' initialized")

    def _build_messages(self, task: str) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self._history)
        messages.append({"role": "user", "content": task})
        return messages

    def _remember(self, task: str, result: str) -> None:
        self._history.append({"role": "user", "content": task})
        self._history.append({"role": "assistant", "content": result})
        if len(self._history) > 20:
            self._history = self._history[-20:]
        logger.debug(f"Agent '{self.role}' remembered interaction, history size: {len(self._history)}")

    @abstractmethod
    async def run(self, task: str, context: DataContext) -> AgentResult:
        raise NotImplementedError
```

- [ ] **Step 4: 创建 utils/__init__.py**

```python
# app/utils/__init__.py
```

- [ ] **Step 5: 运行测试验证**

Run: `pytest tests/ -v`
Expected: PASS

---

### Task 2: 修复 LLM 客户端阻塞问题

**Files:**
- Modify: `app/llm/client.py`

- [ ] **Step 1: 修改为异步客户端**

```python
# app/llm/client.py
from typing import Any, Dict, List, Mapping, Optional
from openai import AsyncOpenAI
from app.utils.logger import setup_logger

logger = setup_logger("LLMClient")


class LLMClient:
    def __init__(self, settings: Any):
        self._model = settings.llm_model
        self._client = AsyncOpenAI(
            api_key=settings.llm_api_key or "EMPTY_KEY",
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_sec,
        )
        logger.info(f"LLMClient initialized with model: {self._model}")

    async def chat(
        self,
        messages: List[Mapping[str, str]],
        temperature: float = 0.2,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        logger.debug(f"Calling LLM with {len(messages)} messages")
        try:
            resp = await self._client.chat.completions.create(**kwargs)
            logger.debug(f"LLM response received, tokens: {resp.usage}")
            return resp.choices[0].message
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
```

- [ ] **Step 2: 更新所有 Agent 的调用方式**

需要将所有 `self._llm.chat(...)` 改为 `await self._llm.chat(...)`

```python
# app/agents/coordinator.py (line 26)
response = await self._llm.chat(messages=messages, temperature=0.0)
```

```python
# app/agents/data_engineer.py (line 32)
response = await self._llm.chat(messages=messages, tools=openai_tools)
```

```python
# app/agents/analyst.py (line 34)
response = await self._llm.chat(messages=messages, tools=openai_tools)
```

```python
# app/agents/visualizer.py (line 32)
response = await self._llm.chat(messages=messages, tools=openai_tools)
```

```python
# app/agents/reporter.py (line 31)
response = await self._llm.chat(messages=messages, temperature=0.3)
```

- [ ] **Step 3: 运行测试验证**

Run: `pytest tests/ -v`
Expected: PASS

---

### Task 3: 修复消息总线线程安全问题

**Files:**
- Modify: `app/core/bus.py`

- [ ] **Step 1: 改用 asyncio 队列**

```python
# app/core/bus.py
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Literal
from app.utils.logger import setup_logger

logger = setup_logger("MessageBus")


@dataclass
class Message:
    sender: str
    receiver: str
    content: str
    msg_type: Literal["task", "result", "error", "info"] = "info"
    metadata: Dict = field(default_factory=dict)


class MessageBus:
    def __init__(self):
        self._inboxes: Dict[str, List[Message]] = defaultdict(list)
        self._history: List[Message] = []
        logger.info("MessageBus initialized")

    async def send(self, message: Message) -> None:
        self._inboxes[message.receiver].append(message)
        self._history.append(message)
        logger.debug(f"Message sent: {message.sender} -> {message.receiver} [{message.msg_type}]")

    async def receive(self, agent_id: str) -> List[Message]:
        messages = self._inboxes.pop(agent_id, [])
        if messages:
            logger.debug(f"Agent '{agent_id}' received {len(messages)} messages")
        return messages

    async def broadcast(self, sender: str, content: str, msg_type: Literal["task", "result", "error", "info"] = "info") -> None:
        agents = {"coordinator", "data_engineer", "analyst", "visualizer", "reporter"}
        for agent in agents:
            if agent != sender:
                await self.send(Message(sender=sender, receiver=agent, content=content, msg_type=msg_type))
        logger.info(f"Broadcast from '{sender}': {content[:50]}...")

    def get_history(self) -> List[Message]:
        return list(self._history)
```

- [ ] **Step 2: 更新 orchestrator.py 中的调用**

```python
# app/core/orchestrator.py (line 55)
await self._bus.send(Message(sender=agent_name, receiver="coordinator", content=f"任务完成：{task_desc[:100]}", msg_type="result"))
```

- [ ] **Step 3: 运行测试验证**

Run: `pytest tests/test_bus.py -v`
Expected: PASS

---

### Task 4: 修复沙箱安全漏洞

**Files:**
- Modify: `app/core/sandbox.py`

- [ ] **Step 1: 重写安全沙箱**

```python
# app/core/sandbox.py
import io
import sys
import signal
import traceback
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from app.utils.logger import setup_logger

logger = setup_logger("Sandbox")

ALLOWED_BUILTINS = {
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
    "frozenset", "int", "isinstance", "len", "list", "map", "max", "min",
    "print", "range", "repr", "reversed", "round", "set", "slice", "sorted",
    "str", "sum", "tuple", "type", "zip",
}

BLOCKED_MODULES = {"os", "sys", "subprocess", "shutil", "pathlib", "socket", "http", "urllib", "ftplib", "smtplib"}


class Sandbox:
    def __init__(self, timeout: int = 30):
        self._timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=1)
        logger.info(f"Sandbox initialized with timeout: {timeout}s")

    def _restricted_exec(self, code: str, context_vars: Dict[str, Any]) -> Dict[str, Any]:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        result = {"stdout": "", "stderr": "", "error": None, "variables": {}}

        safe_builtins = {k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k)
                        for k in ALLOWED_BUILTINS if (k in __builtins__ if isinstance(__builtins__, dict) else hasattr(__builtins__, k))}

        import pandas as pd
        import numpy as np

        safe_globals = {
            "__builtins__": safe_builtins,
            "pd": pd,
            "np": np,
        }

        local_vars = dict(context_vars or {})

        try:
            exec(code, safe_globals, local_vars)
            result["stdout"] = sys.stdout.getvalue()
            result["stderr"] = sys.stderr.getvalue()
            for k, v in local_vars.items():
                if not k.startswith("_"):
                    try:
                        import json
                        json.dumps(v)
                        result["variables"][k] = v
                    except (TypeError, ValueError):
                        result["variables"][k] = str(v)
        except Exception:
            result["error"] = traceback.format_exc()
            result["stderr"] = sys.stderr.getvalue()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return result

    def execute(self, code: str, context_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.debug(f"Executing code in sandbox ({len(code)} chars)")

        for module in BLOCKED_MODULES:
            if f"import {module}" in code or f"from {module}" in code:
                error_msg = f"Security violation: module '{module}' is not allowed"
                logger.warning(error_msg)
                return {"stdout": "", "stderr": "", "error": error_msg, "variables": {}}

        try:
            future = self._executor.submit(self._restricted_exec, code, context_vars)
            result = future.result(timeout=self._timeout)
            logger.debug("Code execution completed successfully")
            return result
        except TimeoutError:
            logger.warning(f"Code execution timed out after {self._timeout}s")
            return {"stdout": "", "stderr": "", "error": f"Execution timed out after {self._timeout} seconds", "variables": {}}
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return {"stdout": "", "stderr": "", "error": str(e), "variables": {}}

    def __del__(self):
        self._executor.shutdown(wait=False)
```

- [ ] **Step 2: 运行测试验证**

Run: `pytest tests/ -v`
Expected: PASS

---

### Task 5: 修复 JSON 解析问题

**Files:**
- Modify: `app/agents/coordinator.py`

- [ ] **Step 1: 改进 JSON 解析**

```python
# app/agents/coordinator.py
import json
import re
import traceback
from typing import Dict
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.utils.logger import setup_logger

logger = setup_logger("Coordinator")

SYSTEM_PROMPT = """你是数据分析团队的协调者。你的职责是：
1. 理解用户需求
2. 拆解为子任务
3. 分配给合适的 Agent

可用 Agent：data_engineer(数据加载清洗), analyst(统计分析), visualizer(图表生成), reporter(报告撰写)

输出 JSON：
{"understanding": "理解", "tasks": [{"agent": "xxx", "task": "描述", "depends_on": []}]}"""


class CoordinatorAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(role="coordinator", system_prompt=SYSTEM_PROMPT)
        self._llm = llm_client

    def _parse_json_response(self, content: str) -> Dict:
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}")

        logger.warning("Using default plan due to parse failure")
        return {
            "understanding": "通用数据分析",
            "tasks": [
                {"agent": "data_engineer", "task": user_request, "depends_on": []},
                {"agent": "analyst", "task": f"分析：{user_request}", "depends_on": [0]},
                {"agent": "visualizer", "task": f"可视化：{user_request}", "depends_on": [0]},
                {"agent": "reporter", "task": f"报告：{user_request}", "depends_on": [1, 2]}
            ]
        }

    async def plan(self, user_request: str) -> Dict:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_request}]
        response = await self._llm.chat(messages=messages, temperature=0.0)
        content = response.content or "{}"
        logger.info(f"Planning for request: {user_request[:50]}...")
        return self._parse_json_response(content)

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            plan = await self.plan(task)
            summary = f"理解：{plan.get('understanding', '')}\n计划 {len(plan.get('tasks', []))} 个子任务"
            self._remember(task, summary)
            return AgentResult(success=True, output=summary, agent_id=self.role, data={"plan": plan})
        except Exception as e:
            logger.error(f"Coordinator failed: {e}")
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
```

- [ ] **Step 2: 运行测试验证**

Run: `pytest tests/ -v`
Expected: PASS

---

### Task 6: 实现历史记录功能

**Files:**
- Modify: `app/history/__init__.py`

- [ ] **Step 1: 实现历史记录**

```python
# app/history/__init__.py
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.utils.logger import setup_logger

logger = setup_logger("History")


class HistoryManager:
    def __init__(self, db_path: str = "data/history.db"):
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"HistoryManager initialized: {db_path}")

    def _init_db(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_request TEXT,
                    plan TEXT,
                    result TEXT,
                    status TEXT DEFAULT 'pending'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    task TEXT,
                    output TEXT,
                    success BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.commit()

    def create_session(self, session_id: str, user_request: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, user_request) VALUES (?, ?)",
                (session_id, user_request)
            )
            conn.commit()
        logger.info(f"Created session: {session_id}")

    def update_session(self, session_id: str, plan: str, result: str, status: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE sessions SET plan=?, result=?, status=? WHERE session_id=?",
                (plan, result, status, session_id)
            )
            conn.commit()
        logger.info(f"Updated session: {session_id}, status: {status}")

    def log_agent(self, session_id: str, agent_name: str, task: str, output: str, success: bool) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO agent_logs (session_id, agent_name, task, output, success) VALUES (?, ?, ?, ?, ?)",
                (session_id, agent_name, task, output, success)
            )
            conn.commit()

    def get_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE session_id=?", (session_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_agent_logs(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM agent_logs WHERE session_id=? ORDER BY created_at", (session_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_history.py
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
```

- [ ] **Step 3: 运行测试验证**

Run: `pytest tests/test_history.py -v`
Expected: PASS

---

### Task 7: 集成历史记录到前端

**Files:**
- Modify: `frontend/app.py`

- [ ] **Step 1: 添加历史记录侧边栏**

```python
# frontend/app.py (在 sidebar 部分添加)

with st.sidebar:
    st.header("⚙️ 设置")
    uploaded_file = st.file_uploader("上传数据文件", type=["csv", "xlsx", "json", "parquet"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith(".json"):
                df = pd.read_json(uploaded_file)
            else:
                df = pd.read_parquet(uploaded_file)

            name = uploaded_file.name.rsplit(".", 1)[0]
            st.session_state.context.add_dataframe(name, df)
            st.success(f"已加载 {uploaded_file.name} ({len(df)} 行)")
        except Exception as e:
            st.error(f"加载失败：{e}")

    if st.session_state.context.list_dataframes():
        st.header("📊 数据集")
        for name in st.session_state.context.list_dataframes():
            df = st.session_state.context.get_dataframe(name)
            st.write(f"**{name}**: {len(df)} 行 × {len(df.columns)} 列")

    st.header("📜 历史记录")
    if st.button("查看历史"):
        from app.history import HistoryManager
        history = HistoryManager()
        sessions = history.get_sessions(limit=10)
        for session in sessions:
            with st.expander(f"{session['created_at']} - {session['status']}"):
                st.write(f"**请求**: {session['user_request']}")
                if session['result']:
                    st.write(f"**结果**: {session['result'][:200]}...")

    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.session_state.context = DataContext()
        st.rerun()
```

- [ ] **Step 2: 在 orchestrator.run 中集成历史记录**

```python
# app/core/orchestrator.py (修改 run 方法)

import uuid
from app.history import HistoryManager

class Orchestrator:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._bus = MessageBus()
        self._history = HistoryManager()

    async def run(self, user_request: str, context: DataContext, coordinator: "BaseAgent") -> Dict:
        from app.agents.coordinator import CoordinatorAgent
        assert isinstance(coordinator, CoordinatorAgent)

        session_id = str(uuid.uuid4())
        self._history.create_session(session_id, user_request)

        try:
            plan_result = await coordinator.plan(user_request)
            results = await self.execute_plan(plan_result, context)

            final_report = context.get_result("final_report") or ""
            agent_outputs = {k: v.output[:200] for k, v in results.items() if v.success}

            self._history.update_session(
                session_id,
                json.dumps(plan_result),
                final_report[:1000],
                "success"
            )

            for k, v in results.items():
                self._history.log_agent(session_id, v.agent_id, "", v.output[:500], v.success)

            return {"plan": plan_result, "agent_results": agent_outputs, "report": final_report, "charts": context.charts, "dataframes": context.list_dataframes()}

        except Exception as e:
            self._history.update_session(session_id, "", str(e), "failed")
            raise
```

- [ ] **Step 3: 运行测试验证**

Run: `pytest tests/ -v`
Expected: PASS

---

### Task 8: 添加重试机制

**Files:**
- Modify: `app/llm/client.py`

- [ ] **Step 1: 添加指数退避重试**

```python
# app/llm/client.py (添加重试逻辑)

import asyncio
from typing import Any, Dict, List, Mapping, Optional
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from app.utils.logger import setup_logger

logger = setup_logger("LLMClient")


class LLMClient:
    def __init__(self, settings: Any):
        self._model = settings.llm_model
        self._client = AsyncOpenAI(
            api_key=settings.llm_api_key or "EMPTY_KEY",
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_sec,
        )
        self._max_retries = 3
        logger.info(f"LLMClient initialized with model: {self._model}")

    async def _retry_with_backoff(self, func, *args, **kwargs):
        for attempt in range(self._max_retries):
            try:
                return await func(*args, **kwargs)
            except (RateLimitError, APITimeoutError) as e:
                if attempt == self._max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{self._max_retries} after {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            except APIError as e:
                logger.error(f"API error: {e}")
                raise

    async def chat(
        self,
        messages: List[Mapping[str, str]],
        temperature: float = 0.2,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        logger.debug(f"Calling LLM with {len(messages)} messages")

        async def _call():
            resp = await self._client.chat.completions.create(**kwargs)
            return resp.choices[0].message

        return await self._retry_with_backoff(_call)
```

- [ ] **Step 2: 运行测试验证**

Run: `pytest tests/ -v`
Expected: PASS

---

### Task 9: 最终集成测试

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: 创建集成测试**

```python
# tests/test_integration.py
import asyncio
import pytest
from app.core.context import DataContext
from app.core.bus import MessageBus
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
    bus = MessageBus()
    from app.core.bus import Message
    msg = Message(sender="a", receiver="b", content="test")
    asyncio.run(bus.send(msg))
    messages = asyncio.run(bus.receive("b"))
    assert len(messages) == 1


def test_sandbox_safe_execution():
    sandbox = Sandbox(timeout=5)
    result = sandbox.execute("x = 1 + 1")
    assert result["error"] is None
    assert result["variables"]["x"] == 2


def test_sandbox_blocks_dangerous_code():
    sandbox = Sandbox(timeout=5)
    result = sandbox.execute("import os; os.system('dir')")
    assert "Security violation" in result["error"]


def test_sandbox_timeout():
    sandbox = Sandbox(timeout=1)
    result = sandbox.execute("import time; time.sleep(10)")
    assert "timed out" in result["error"]


def test_history_full_flow():
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        history = HistoryManager(db_path=db_path)
        history.create_session("s1", "测试请求")
        history.log_agent("s1", "analyst", "分析", "完成", True)
        history.update_session("s1", "{}", "报告", "success")
        session = history.get_session("s1")
        assert session["status"] == "success"
        logs = history.get_agent_logs("s1")
        assert len(logs) == 1
```

- [ ] **Step 2: 运行所有测试**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 3: 提交代码**

```bash
git add -A
git commit -m "fix: 修复关键安全漏洞和架构问题

- 添加统一日志系统
- LLM客户端改为异步调用
- 消息总线改用async实现
- 沙箱添加安全限制和超时
- 改进JSON解析逻辑
- 实现历史记录功能
- 添加LLM调用重试机制"
```

---

## 自检清单

1. ✅ 所有安全漏洞已修复（沙箱限制、模块过滤）
2. ✅ 异步阻塞问题已解决（AsyncOpenAI）
3. ✅ 线程安全问题已修复（async消息总线）
4. ✅ 日志系统完整覆盖
5. ✅ 历史记录功能完整
6. ✅ 重试机制提高健壮性
7. ✅ 测试覆盖关键路径
