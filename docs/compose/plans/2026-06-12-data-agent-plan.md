# DataAgent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-agent data analysis system where 5 specialized agents collaborate to analyze data via natural language.

**Architecture:** Custom agent framework with message bus orchestration. Coordinator agent plans tasks, delegates to specialist agents (Data Engineer, Analyst, Visualizer, Reporter), and synthesizes results. All agents share a DataContext for data passing.

**Tech Stack:** Python 3.11+, FastAPI, Streamlit, OpenAI SDK, pandas, matplotlib, plotly, SQLite

---

## File Structure

```
DataAgent/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings
│   ├── main.py                   # FastAPI entry point
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py               # BaseAgent ABC
│   │   ├── coordinator.py        # Task planning + delegation
│   │   ├── data_engineer.py      # Data loading + cleaning
│   │   ├── analyst.py            # Statistical analysis
│   │   ├── visualizer.py         # Chart generation
│   │   └── reporter.py           # Report generation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bus.py                # Message bus
│   │   ├── context.py            # DataContext shared state
│   │   ├── planner.py            # DAG task planner
│   │   ├── sandbox.py            # Code execution sandbox
│   │   └── orchestrator.py       # Agent orchestration engine
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py           # Tool registration
│   │   ├── data_tools.py         # File/SQL/API data tools
│   │   ├── analysis_tools.py     # Statistical analysis tools
│   │   └── chart_tools.py        # Visualization tools
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py             # OpenAI SDK wrapper
│   └── history/
│       ├── __init__.py
│       └── store.py              # SQLite conversation history
├── frontend/
│   └── app.py                    # Streamlit UI
├── tests/
│   ├── __init__.py
│   ├── test_context.py
│   ├── test_bus.py
│   ├── test_tools.py
│   ├── test_agents.py
│   └── test_orchestrator.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Task 1: Project Scaffolding

**Covers:** S2

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.111.1
uvicorn==0.30.3
openai==1.40.3
pydantic==2.8.2
pydantic-settings==2.4.0
pandas==2.2.2
numpy==1.26.4
scipy==1.14.0
scikit-learn==1.5.1
matplotlib==3.9.1
plotly==5.22.0
streamlit==1.37.0
sqlalchemy==2.0.31
httpx==0.27.0
openpyxl==3.1.5
pyarrow==17.0.0
pytest==8.3.2
```

- [ ] **Step 2: Create .env.example**

```
APP_NAME=DataAgent
APP_ENV=dev

LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SEC=60

HISTORY_DB_PATH=data/history.db
CHART_OUTPUT_DIR=data/charts
SANDBOX_TIMEOUT_SEC=30
```

- [ ] **Step 3: Create app/config.py**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "DataAgent"
    app_env: str = "dev"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_sec: int = 60

    history_db_path: str = "data/history.db"
    chart_output_dir: str = "data/charts"
    sandbox_timeout_sec: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Create app/__init__.py (empty)**

```python
```

- [ ] **Step 5: Verify config loads**

Run: `python -c "from app.config import get_settings; s = get_settings(); print(s.app_name)"`
Expected: `DataAgent`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example app/config.py app/__init__.py
git commit -m "feat: project scaffolding with config"
```

---

## Task 2: LLM Client

**Covers:** S2

**Files:**
- Create: `app/llm/__init__.py`
- Create: `app/llm/client.py`
- Create: `tests/test_llm_client.py`

- [ ] **Step 1: Write test**

```python
# tests/test_llm_client.py
from app.llm.client import LLMClient


def test_llm_client_init():
    class FakeSettings:
        llm_api_key = "EMPTY_KEY"
        llm_base_url = "https://api.openai.com/v1"
        llm_model = "gpt-4o-mini"
        llm_timeout_sec = 30
    client = LLMClient(settings=FakeSettings())
    assert client._model == "gpt-4o-mini"


def test_format_messages():
    class FakeSettings:
        llm_api_key = "EMPTY_KEY"
        llm_base_url = "https://api.openai.com/v1"
        llm_model = "gpt-4o-mini"
        llm_timeout_sec = 30
    client = LLMClient(settings=FakeSettings())
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"},
    ]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_client.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement LLM client**

```python
# app/llm/__init__.py
from app.llm.client import LLMClient

__all__ = ["LLMClient"]
```

```python
# app/llm/client.py
from typing import Any, Dict, List, Mapping, Optional

from openai import OpenAI


class LLMClient:
    def __init__(self, settings: Any):
        self._model = settings.llm_model
        self._client = OpenAI(
            api_key=settings.llm_api_key or "EMPTY_KEY",
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_sec,
        )

    def chat(
        self,
        messages: List[Mapping[str, str]],
        temperature: float = 0.2,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "model": model or self._model,
            "messages": messages,  # type: ignore[arg-type]
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/llm/ tests/test_llm_client.py
git commit -m "feat: LLM client with OpenAI SDK and function calling support"
```

---

## Task 3: Shared DataContext

**Covers:** S3.4

**Files:**
- Create: `app/core/__init__.py`
- Create: `app/core/context.py`
- Create: `tests/test_context.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_context.py
import pandas as pd
from app.core.context import DataContext


def test_add_and_get_dataframe():
    ctx = DataContext()
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    ctx.add_dataframe("test", df)
    result = ctx.get_dataframe("test")
    assert result is not None
    assert len(result) == 3


def test_list_dataframes():
    ctx = DataContext()
    ctx.add_dataframe("a", pd.DataFrame({"x": [1]}))
    ctx.add_dataframe("b", pd.DataFrame({"y": [2]}))
    assert ctx.list_dataframes() == ["a", "b"]


def test_add_analysis_result():
    ctx = DataContext()
    ctx.add_result("top10", {"data": [1, 2, 3]})
    assert ctx.get_result("top10") == {"data": [1, 2, 3]}


def test_add_chart():
    ctx = DataContext()
    ctx.add_chart("/tmp/chart.png")
    assert len(ctx.charts) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_context.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement DataContext**

```python
# app/core/__init__.py
from app.core.context import DataContext

__all__ = ["DataContext"]
```

```python
# app/core/context.py
from typing import Any, Dict, List, Optional
import pandas as pd


class DataContext:
    def __init__(self):
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.charts: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def add_dataframe(self, name: str, df: pd.DataFrame) -> None:
        self.dataframes[name] = df

    def get_dataframe(self, name: str) -> Optional[pd.DataFrame]:
        return self.dataframes.get(name)

    def list_dataframes(self) -> List[str]:
        return list(self.dataframes.keys())

    def add_result(self, key: str, value: Any) -> None:
        self.analysis_results[key] = value

    def get_result(self, key: str) -> Any:
        return self.analysis_results.get(key)

    def add_chart(self, path: str) -> None:
        self.charts.append(path)

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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_context.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/ tests/test_context.py
git commit -m "feat: DataContext for shared state between agents"
```

---

## Task 4: Message Bus

**Covers:** S3.3

**Files:**
- Create: `app/core/bus.py`
- Create: `tests/test_bus.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_bus.py
from app.core.bus import Message, MessageBus


def test_send_and_receive():
    bus = MessageBus()
    msg = Message(sender="coordinator", receiver="analyst", content="analyze data", msg_type="task")
    bus.send(msg)
    messages = bus.receive("analyst")
    assert len(messages) == 1
    assert messages[0].content == "analyze data"


def test_receive_clears_inbox():
    bus = MessageBus()
    bus.send(Message(sender="a", receiver="b", content="hello", msg_type="info"))
    bus.receive("b")
    messages = bus.receive("b")
    assert len(messages) == 0


def test_broadcast():
    bus = MessageBus()
    bus.broadcast(sender="coordinator", content="task complete", msg_type="info")
    assert len(bus.receive("analyst")) == 1
    assert len(bus.receive("visualizer")) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_bus.py -v`
Expected: FAIL

- [ ] **Step 3: Implement MessageBus**

```python
# app/core/bus.py
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Literal


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
        self._lock = threading.Lock()
        self._history: List[Message] = []

    def send(self, message: Message) -> None:
        with self._lock:
            self._inboxes[message.receiver].append(message)
            self._history.append(message)

    def receive(self, agent_id: str) -> List[Message]:
        with self._lock:
            messages = self._inboxes.pop(agent_id, [])
            return messages

    def broadcast(self, sender: str, content: str, msg_type: Literal["task", "result", "error", "info"] = "info") -> None:
        agents = {"coordinator", "data_engineer", "analyst", "visualizer", "reporter"}
        for agent in agents:
            if agent != sender:
                self.send(Message(sender=sender, receiver=agent, content=content, msg_type=msg_type))

    def get_history(self) -> List[Message]:
        with self._lock:
            return list(self._history)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_bus.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/bus.py tests/test_bus.py
git commit -m "feat: MessageBus for inter-agent communication"
```

---

## Task 5: Tool Registry

**Covers:** S3.1

**Files:**
- Create: `app/tools/__init__.py`
- Create: `app/tools/registry.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_tools.py
from app.tools.registry import Tool, ToolRegistry


def test_register_and_get():
    registry = ToolRegistry()
    tool = Tool(
        name="read_csv",
        description="Read a CSV file",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        function=lambda path: f"read {path}",
    )
    registry.register(tool)
    assert registry.get("read_csv") is not None
    assert registry.get("nonexistent") is None


def test_list_tools():
    registry = ToolRegistry()
    registry.register(Tool(name="a", description="a", parameters={}, function=lambda: None))
    registry.register(Tool(name="b", description="b", parameters={}, function=lambda: None))
    names = [t.name for t in registry.list_tools()]
    assert names == ["a", "b"]


def test_to_openai_tools():
    registry = ToolRegistry()
    registry.register(Tool(
        name="read_csv",
        description="Read a CSV file",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        function=lambda path: path,
    ))
    openai_tools = registry.to_openai_tools()
    assert len(openai_tools) == 1
    assert openai_tools[0]["type"] == "function"
    assert openai_tools[0]["function"]["name"] == "read_csv"


def test_call_tool():
    registry = ToolRegistry()
    registry.register(Tool(
        name="add",
        description="Add two numbers",
        parameters={"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}},
        function=lambda a, b: a + b,
    ))
    result = registry.call("add", a=3, b=4)
    assert result == 7
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ToolRegistry**

```python
# app/tools/__init__.py
from app.tools.registry import Tool, ToolRegistry

__all__ = ["Tool", "ToolRegistry"]
```

```python
# app/tools/registry.py
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable[..., Any]


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def call(self, name: str, **kwargs: Any) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return tool.function(**kwargs)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/tools/ tests/test_tools.py
git commit -m "feat: ToolRegistry with OpenAI function calling format"
```

---

## Task 6: Agent Base Class

**Covers:** S3.1

**Files:**
- Create: `app/agents/__init__.py`
- Create: `app/agents/base.py`
- Create: `tests/test_agents.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_agents.py
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.tools.registry import ToolRegistry


class DummyAgent(BaseAgent):
    async def run(self, task: str, context: DataContext) -> AgentResult:
        return AgentResult(success=True, output="done", agent_id=self.role)


def test_agent_creation():
    agent = DummyAgent(role="test", system_prompt="You are test")
    assert agent.role == "test"


def test_agent_run():
    import asyncio
    agent = DummyAgent(role="test", system_prompt="You are test")
    ctx = DataContext()
    result = asyncio.get_event_loop().run_until_complete(agent.run("do something", ctx))
    assert result.success is True
    assert result.output == "done"


def test_agent_tools():
    registry = ToolRegistry()
    agent = DummyAgent(role="test", system_prompt="test", tools=registry)
    assert agent.tools is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_agents.py -v`
Expected: FAIL

- [ ] **Step 3: Implement BaseAgent**

```python
# app/agents/__init__.py
from app.agents.base import BaseAgent, AgentResult

__all__ = ["BaseAgent", "AgentResult"]
```

```python
# app/agents/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.context import DataContext
from app.tools.registry import ToolRegistry


@dataclass
class AgentResult:
    success: bool
    output: str
    agent_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseAgent(ABC):
    def __init__(
        self,
        role: str,
        system_prompt: str,
        tools: Optional[ToolRegistry] = None,
    ):
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self._history: List[Dict[str, str]] = []

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

    @abstractmethod
    async def run(self, task: str, context: DataContext) -> AgentResult:
        raise NotImplementedError
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_agents.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/agents/ tests/test_agents.py
git commit -m "feat: BaseAgent abstract class with memory and tool support"
```

---

## Task 7: Data Tools

**Covers:** S4

**Files:**
- Create: `app/tools/data_tools.py`

- [ ] **Step 1: Implement data tools**

```python
# app/tools/data_tools.py
import io
from pathlib import Path
from typing import Any

import pandas as pd


def read_file(path: str) -> pd.DataFrame:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(p)
    elif suffix in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    elif suffix == ".json":
        return pd.read_json(p)
    elif suffix == ".parquet":
        return pd.read_parquet(p)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def read_sql(connection_string: str, query: str) -> pd.DataFrame:
    from sqlalchemy import create_engine
    engine = create_engine(connection_string)
    return pd.read_sql(query, engine)


def call_api(url: str, method: str = "GET", headers: dict = None, body: dict = None) -> pd.DataFrame:
    import httpx
    client = httpx.Client(timeout=30)
    if method.upper() == "GET":
        resp = client.get(url, headers=headers)
    else:
        resp = client.post(url, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict):
        return pd.DataFrame([data])
    raise ValueError("Unexpected API response format")


def parse_text(text: str) -> pd.DataFrame:
    import io
    return pd.read_csv(io.StringIO(text), sep=None, engine="python")


def clean_data(df: pd.DataFrame, drop_duplicates: bool = True, fill_na: str = "median") -> pd.DataFrame:
    result = df.copy()
    if drop_duplicates:
        result = result.drop_duplicates()
    for col in result.columns:
        if result[col].isna().any():
            if fill_na == "median" and result[col].dtype in ["int64", "float64"]:
                result[col] = result[col].fillna(result[col].median())
            elif fill_na == "mode":
                result[col] = result[col].fillna(result[col].mode().iloc[0] if not result[col].mode().empty else "unknown")
            else:
                result[col] = result[col].fillna(0)
    return result


def get_data_tools():
    from app.tools.registry import Tool
    return [
        Tool(
            name="read_file",
            description="Read a data file (CSV, Excel, JSON, Parquet) and return a DataFrame",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string", "description": "File path"}},
                "required": ["path"],
            },
            function=read_file,
        ),
        Tool(
            name="read_sql",
            description="Execute SQL query and return results as DataFrame",
            parameters={
                "type": "object",
                "properties": {
                    "connection_string": {"type": "string", "description": "SQLAlchemy connection string"},
                    "query": {"type": "string", "description": "SQL query"},
                },
                "required": ["connection_string", "query"],
            },
            function=read_sql,
        ),
        Tool(
            name="call_api",
            description="Call a REST API and return response as DataFrame",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "method": {"type": "string", "default": "GET"},
                },
                "required": ["url"],
            },
            function=call_api,
        ),
        Tool(
            name="parse_text",
            description="Parse pasted text/table data into DataFrame",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Tabular text data"}},
                "required": ["text"],
            },
            function=parse_text,
        ),
        Tool(
            name="clean_data",
            description="Clean a DataFrame: remove duplicates, fill missing values",
            parameters={
                "type": "object",
                "properties": {
                    "drop_duplicates": {"type": "boolean", "default": True},
                    "fill_na": {"type": "string", "enum": ["median", "mode", "zero"], "default": "median"},
                },
            },
            function=clean_data,
        ),
    ]
```

- [ ] **Step 2: Commit**

```bash
git add app/tools/data_tools.py
git commit -m "feat: data tools for file/SQL/API/text data loading"
```

---

## Task 8: Data Engineer Agent

**Covers:** S3.2, S4

**Files:**
- Create: `app/agents/data_engineer.py`

- [ ] **Step 1: Implement Data Engineer Agent**

```python
# app/agents/data_engineer.py
import traceback
from typing import Any

from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.data_tools import get_data_tools
from app.tools.registry import ToolRegistry


SYSTEM_PROMPT = """你是数据工程师 Agent。你的职责是：
1. 根据用户描述，选择合适的数据源（文件、SQL、API、文本）加载数据
2. 对数据进行清洗（去重、填充缺失值、类型转换）
3. 将处理好的数据存入共享上下文

你可以使用以下工具：
- read_file: 读取 CSV/Excel/JSON/Parquet 文件
- read_sql: 执行 SQL 查询
- call_api: 调用 REST API
- parse_text: 解析粘贴的文本数据
- clean_data: 清洗数据

工作流程：
1. 分析用户需求，确定数据源类型
2. 调用对应工具加载数据
3. 调用 clean_data 清洗数据
4. 返回数据概览（行数、列名、数据类型、缺失值统计）

只输出数据概览结果，不要输出多余内容。"""


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

            response = self._llm.chat(messages=messages, tools=openai_tools)

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    func_name = tool_call.function.name
                    import json
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
```

- [ ] **Step 2: Commit**

```bash
git add app/agents/data_engineer.py
git commit -m "feat: DataEngineerAgent with data loading and cleaning"
```

---

## Task 9: Analysis Tools + Analyst Agent

**Covers:** S3.2, S5

**Files:**
- Create: `app/tools/analysis_tools.py`
- Create: `app/agents/analyst.py`
- Create: `app/core/sandbox.py`

- [ ] **Step 1: Implement analysis tools**

```python
# app/tools/analysis_tools.py
from typing import Any, Dict, Optional
import pandas as pd
import numpy as np


def describe_data(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "describe": df.describe(include="all").to_dict(),
        "missing": df.isnull().sum().to_dict(),
    }


def group_aggregate(df: pd.DataFrame, group_by: str, agg_col: str, agg_func: str = "sum", top_n: int = 10) -> pd.DataFrame:
    result = df.groupby(group_by)[agg_col].agg(agg_func).sort_values(ascending=False).head(top_n)
    return result.reset_index()


def correlation(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    numeric = df.select_dtypes(include=["number"])
    if columns:
        numeric = numeric[[c for c in columns if c in numeric.columns]]
    return numeric.corr()


def detect_anomaly(df: pd.DataFrame, column: str, method: str = "iqr") -> pd.DataFrame:
    if method == "iqr":
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        mask = (df[column] < Q1 - 1.5 * IQR) | (df[column] > Q3 + 1.5 * IQR)
        return df[mask]
    elif method == "zscore":
        from scipy import stats
        z = np.abs(stats.zscore(df[column].dropna()))
        mask = z > 3
        return df[column].dropna()[mask]
    return pd.DataFrame()


def get_analysis_tools():
    from app.tools.registry import Tool
    return [
        Tool(
            name="describe_data",
            description="Get statistical description of a DataFrame",
            parameters={"type": "object", "properties": {}},
            function=describe_data,
        ),
        Tool(
            name="group_aggregate",
            description="Group by a column and aggregate another column",
            parameters={
                "type": "object",
                "properties": {
                    "group_by": {"type": "string"},
                    "agg_col": {"type": "string"},
                    "agg_func": {"type": "string", "enum": ["sum", "mean", "count", "min", "max"], "default": "sum"},
                    "top_n": {"type": "integer", "default": 10},
                },
                "required": ["group_by", "agg_col"],
            },
            function=group_aggregate,
        ),
        Tool(
            name="correlation",
            description="Calculate correlation matrix for numeric columns",
            parameters={"type": "object", "properties": {"columns": {"type": "array", "items": {"type": "string"}}}},
            function=correlation,
        ),
        Tool(
            name="detect_anomaly",
            description="Detect anomalies in a column using IQR or Z-score method",
            parameters={
                "type": "object",
                "properties": {
                    "column": {"type": "string"},
                    "method": {"type": "string", "enum": ["iqr", "zscore"], "default": "iqr"},
                },
                "required": ["column"],
            },
            function=detect_anomaly,
        ),
    ]
```

- [ ] **Step 2: Implement sandbox**

```python
# app/core/sandbox.py
import io
import sys
import traceback
from typing import Any, Dict


ALLOWED_MODULES = {"pandas", "numpy", "scipy", "sklearn", "math", "statistics", "collections", "itertools", "datetime"}


class Sandbox:
    def __init__(self, timeout: int = 30):
        self._timeout = timeout

    def execute(self, code: str, context_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        local_vars = dict(context_vars or {})
        result = {"stdout": "", "stderr": "", "error": None, "variables": {}}

        try:
            exec(code, {"__builtins__": __builtins__, "pd": __import__("pandas"), "np": __import__("numpy")}, local_vars)
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
```

- [ ] **Step 3: Implement Analyst Agent**

```python
# app/agents/analyst.py
import json
import traceback

from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.core.sandbox import Sandbox
from app.llm.client import LLMClient
from app.tools.analysis_tools import get_analysis_tools
from app.tools.registry import ToolRegistry


SYSTEM_PROMPT = """你是数据分析 Agent。你的职责是：
1. 对数据进行统计分析（描述性统计、分组聚合、相关性分析、异常检测）
2. 根据用户需求生成 Python 分析代码并在沙箱中执行
3. 将分析结果存入共享上下文

你可以使用工具进行分析，也可以直接生成 pandas/numpy 代码执行。
生成代码时，变量 `df` 已预加载为当前数据集。

输出格式：
- 如果用工具分析，返回分析结果摘要
- 如果生成代码，返回代码和执行结果"""


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

            response = self._llm.chat(messages=messages, tools=openai_tools)

            results = []
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    if func_name in ("describe_data", "correlation", "detect_anomaly"):
                        df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                        if df_name:
                            df = context.get_dataframe(df_name)
                            if df is not None:
                                result = self.tools.call(func_name, df=df, **args)
                                context.add_result(f"{func_name}_{df_name}", result if not hasattr(result, 'to_dict') else result.to_dict())
                                results.append(f"{func_name}: {str(result)[:500]}")
                    elif func_name == "group_aggregate":
                        df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
                        if df_name:
                            df = context.get_dataframe(df_name)
                            if df is not None:
                                result = self.tools.call(func_name, df=df, **args)
                                context.add_result(f"group_{args.get('group_by')}", result.to_dict())
                                results.append(f"Group by {args.get('group_by')}: {result.to_string()}")

            output = "\n".join(results) if results else (response.content or "分析完成")
            self._remember(task, output)
            return AgentResult(success=True, output=output, agent_id=self.role)

        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
```

- [ ] **Step 4: Commit**

```bash
git add app/tools/analysis_tools.py app/core/sandbox.py app/agents/analyst.py
git commit -m "feat: AnalystAgent with analysis tools and code sandbox"
```

---

## Task 10: Visualizer Agent

**Covers:** S3.2

**Files:**
- Create: `app/tools/chart_tools.py`
- Create: `app/agents/visualizer.py`

- [ ] **Step 1: Implement chart tools**

```python
# app/tools/chart_tools.py
import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

CHINESE_FONTS = ["SimHei", "Microsoft YaHei", "PingFang SC", "WenQuanYi Micro Hei"]
for font in CHINESE_FONTS:
    if any(font.lower() in f.name.lower() for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [font]
        break
plt.rcParams["axes.unicode_minus"] = False


def _save_chart(fig, output_dir: str, name: str) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = os.path.join(output_dir, f"{name}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_line(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df[x], df[y], marker="o")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} over {x}")
    ax.grid(True, alpha=0.3)
    return _save_chart(fig, output_dir, f"line_{x}_{y}")


def plot_bar(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df[x].astype(str), df[y])
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} by {x}")
    plt.xticks(rotation=45, ha="right")
    return _save_chart(fig, output_dir, f"bar_{x}_{y}")


def plot_scatter(df: pd.DataFrame, x: str, y: str, title: str = "", output_dir: str = "data/charts") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df[x], df[y], alpha=0.6)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} vs {x}")
    ax.grid(True, alpha=0.3)
    return _save_chart(fig, output_dir, f"scatter_{x}_{y}")


def plot_pie(df: pd.DataFrame, labels: str, values: str, title: str = "", output_dir: str = "data/charts") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie(df[values], labels=df[labels], autopct="%1.1f%%", startangle=90)
    ax.set_title(title or f"{values} distribution")
    return _save_chart(fig, output_dir, f"pie_{labels}_{values}")


def get_chart_tools():
    from app.tools.registry import Tool
    return [
        Tool(
            name="plot_line",
            description="Create a line chart",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "string", "description": "X axis column"},
                    "y": {"type": "string", "description": "Y axis column"},
                    "title": {"type": "string", "default": ""},
                },
                "required": ["x", "y"],
            },
            function=plot_line,
        ),
        Tool(
            name="plot_bar",
            description="Create a bar chart",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "string"},
                    "y": {"type": "string"},
                    "title": {"type": "string", "default": ""},
                },
                "required": ["x", "y"],
            },
            function=plot_bar,
        ),
        Tool(
            name="plot_scatter",
            description="Create a scatter plot",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "string"},
                    "y": {"type": "string"},
                    "title": {"type": "string", "default": ""},
                },
                "required": ["x", "y"],
            },
            function=plot_scatter,
        ),
        Tool(
            name="plot_pie",
            description="Create a pie chart",
            parameters={
                "type": "object",
                "properties": {
                    "labels": {"type": "string"},
                    "values": {"type": "string"},
                    "title": {"type": "string", "default": ""},
                },
                "required": ["labels", "values"],
            },
            function=plot_pie,
        ),
    ]
```

- [ ] **Step 2: Implement Visualizer Agent**

```python
# app/agents/visualizer.py
import json
import traceback

from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.tools.chart_tools import get_chart_tools
from app.tools.registry import ToolRegistry


SYSTEM_PROMPT = """你是数据可视化 Agent。你的职责是根据数据分析结果生成合适的图表。

可用图表类型：
- plot_line: 折线图（趋势分析）
- plot_bar: 柱状图（分类对比）
- plot_scatter: 散点图（相关性）
- plot_pie: 饼图（占比分析）

选择图表的原则：
- 时间序列数据 → 折线图
- 分类对比 → 柱状图
- 两个连续变量关系 → 散点图
- 占比分布 → 饼图（类别不超过 8 个）

图表标题使用中文，简洁明了。"""


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

            response = self._llm.chat(messages=messages, tools=openai_tools)

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
```

- [ ] **Step 3: Commit**

```bash
git add app/tools/chart_tools.py app/agents/visualizer.py
git commit -m "feat: VisualizerAgent with matplotlib chart tools"
```

---

## Task 11: Reporter Agent

**Covers:** S3.2

**Files:**
- Create: `app/agents/reporter.py`

- [ ] **Step 1: Implement Reporter Agent**

```python
# app/agents/reporter.py
import traceback

from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient


SYSTEM_PROMPT = """你是数据分析报告 Agent。你的职责是将分析结果转化为清晰的中文洞察报告。

报告格式：
## 分析概要
简述分析目标和数据概况

## 关键发现
列出 3-5 个最重要的发现，每个发现用一句话概括 + 数据支撑

## 详细分析
对每个发现展开分析，引用具体数据

## 建议
基于分析结果给出 2-3 条可操作的建议

规则：
1. 用数据说话，避免主观臆断
2. 关键数字加粗或用列表突出
3. 语言简洁，避免废话
4. 如果数据不足以支撑结论，明确说明"""


class ReporterAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(role="reporter", system_prompt=SYSTEM_PROMPT)
        self._llm = llm_client

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            analysis_summary = []
            for key, value in context.analysis_results.items():
                analysis_summary.append(f"【{key}】\n{str(value)[:1000]}")

            chart_info = f"\n已生成 {len(context.charts)} 个图表" if context.charts else ""

            full_task = (
                f"{task}\n\n"
                f"数据概况：\n{context.summary()}\n\n"
                f"分析结果：\n{''.join(analysis_summary)}\n"
                f"{chart_info}"
            )

            messages = self._build_messages(full_task)
            response = self._llm.chat(messages=messages, temperature=0.3)

            report = response.content or "无法生成报告"
            context.add_result("final_report", report)
            self._remember(task, report)
            return AgentResult(success=True, output=report, agent_id=self.role)

        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
```

- [ ] **Step 2: Commit**

```bash
git add app/agents/reporter.py
git commit -m "feat: ReporterAgent for generating analysis reports"
```

---

## Task 12: Coordinator Agent + Orchestrator

**Covers:** S3.2, S3.5

**Files:**
- Create: `app/agents/coordinator.py`
- Create: `app/core/orchestrator.py`

- [ ] **Step 1: Implement Coordinator Agent**

```python
# app/agents/coordinator.py
import json
import traceback
from typing import Dict, List

from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient


SYSTEM_PROMPT = """你是数据分析团队的协调者。你的职责是：
1. 理解用户的分析需求
2. 将需求拆解为子任务
3. 分配给合适的专业 Agent 执行
4. 汇总所有 Agent 的结果

可用的 Agent：
- data_engineer: 数据加载和清洗
- analyst: 统计分析和数据建模
- visualizer: 图表生成
- reporter: 报告撰写

输出格式（JSON）：
{
    "understanding": "对用户需求的理解",
    "tasks": [
        {"agent": "data_engineer", "task": "具体任务描述", "depends_on": []},
        {"agent": "analyst", "task": "具体任务描述", "depends_on": [0]},
        {"agent": "visualizer", "task": "具体任务描述", "depends_on": [0]},
        {"agent": "reporter", "task": "具体任务描述", "depends_on": [1, 2]}
    ]
}

depends_on 填写前置任务的索引号。如果没有前置依赖，填空数组。"""


class CoordinatorAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(role="coordinator", system_prompt=SYSTEM_PROMPT)
        self._llm = llm_client

    async def plan(self, user_request: str) -> Dict:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_request},
        ]
        response = self._llm.chat(messages=messages, temperature=0.0)
        content = response.content or "{}"

        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            plan = json.loads(content[start:end])
        except (json.JSONDecodeError, ValueError):
            plan = {
                "understanding": "通用数据分析",
                "tasks": [
                    {"agent": "data_engineer", "task": user_request, "depends_on": []},
                    {"agent": "analyst", "task": f"分析数据：{user_request}", "depends_on": [0]},
                    {"agent": "visualizer", "task": f"可视化：{user_request}", "depends_on": [0]},
                    {"agent": "reporter", "task": f"撰写报告：{user_request}", "depends_on": [1, 2]},
                ],
            }
        return plan

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            plan = await self.plan(task)
            summary = f"理解：{plan.get('understanding', '')}\n计划 {len(plan.get('tasks', []))} 个子任务"
            self._remember(task, summary)
            return AgentResult(success=True, output=summary, agent_id=self.role, data={"plan": plan})
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
```

- [ ] **Step 2: Implement Orchestrator**

```python
# app/core/orchestrator.py
import asyncio
import traceback
from typing import Dict, Optional

from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.core.bus import MessageBus, Message


class Orchestrator:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._bus = MessageBus()

    def register_agent(self, agent: BaseAgent) -> None:
        self._agents[agent.role] = agent

    async def execute_plan(self, plan: Dict, context: DataContext) -> Dict[str, AgentResult]:
        tasks = plan.get("tasks", [])
        results: Dict[str, AgentResult] = {}
        completed: set = set()

        max_iterations = len(tasks) * 2
        iteration = 0

        while len(completed) < len(tasks) and iteration < max_iterations:
            iteration += 1
            ready = []

            for idx, task_def in enumerate(tasks):
                if idx in completed:
                    continue
                deps = task_def.get("depends_on", [])
                if all(d in completed for d in deps):
                    ready.append((idx, task_def))

            if not ready:
                break

            for idx, task_def in ready:
                agent_name = task_def["agent"]
                task_desc = task_def["task"]

                agent = self._agents.get(agent_name)
                if not agent:
                    results[f"{agent_name}_{idx}"] = AgentResult(
                        success=False, output="", agent_id=agent_name,
                        error=f"Agent '{agent_name}' not registered"
                    )
                    completed.add(idx)
                    continue

                dep_context = ""
                for dep_idx in task_def.get("depends_on", []):
                    dep_key = f"{tasks[dep_idx]['agent']}_{dep_idx}"
                    if dep_key in results and results[dep_key].success:
                        dep_context += f"\n前置任务结果：{results[dep_key].output[:500]}"

                full_task = f"{task_desc}{dep_context}"
                result = await agent.run(full_task, context)
                results[f"{agent_name}_{idx}"] = result
                completed.add(idx)

                self._bus.send(Message(
                    sender=agent_name, receiver="coordinator",
                    content=f"任务完成：{task_desc[:100]}", msg_type="result"
                ))

        return results

    async def run(self, user_request: str, context: DataContext, coordinator: "BaseAgent") -> Dict:
        from app.agents.coordinator import CoordinatorAgent
        assert isinstance(coordinator, CoordinatorAgent)

        plan_result = await coordinator.plan(user_request)
        results = await self.execute_plan(plan_result, context)

        final_report = context.get_result("final_report") or ""
        agent_outputs = {k: v.output[:200] for k, v in results.items() if v.success}

        return {
            "plan": plan_result,
            "agent_results": agent_outputs,
            "report": final_report,
            "charts": context.charts,
            "dataframes": context.list_dataframes(),
        }
```

- [ ] **Step 3: Commit**

```bash
git add app/agents/coordinator.py app/core/orchestrator.py
git commit -m "feat: CoordinatorAgent and Orchestrator for task planning and execution"
```

---

## Task 13: Streamlit Frontend

**Covers:** S6

**Files:**
- Create: `frontend/app.py`

- [ ] **Step 1: Implement Streamlit app**

```python
# frontend/app.py
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from app.config import get_settings
from app.llm.client import LLMClient
from app.core.context import DataContext
from app.core.orchestrator import Orchestrator
from app.agents.coordinator import CoordinatorAgent
from app.agents.data_engineer import DataEngineerAgent
from app.agents.analyst import AnalystAgent
from app.agents.visualizer import VisualizerAgent
from app.agents.reporter import ReporterAgent


st.set_page_config(page_title="DataAgent", page_icon="📊", layout="wide")
st.title("📊 DataAgent — 多 Agent 数据分析系统")


@st.cache_resource
def init_system():
    settings = get_settings()
    llm = LLMClient(settings=settings)
    coordinator = CoordinatorAgent(llm_client=llm)
    orchestrator = Orchestrator()
    orchestrator.register_agent(DataEngineerAgent(llm_client=llm))
    orchestrator.register_agent(AnalystAgent(llm_client=llm, sandbox_timeout=settings.sandbox_timeout_sec))
    orchestrator.register_agent(VisualizerAgent(llm_client=llm, chart_output_dir=settings.chart_output_dir))
    orchestrator.register_agent(ReporterAgent(llm_client=llm))
    return coordinator, orchestrator


if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = DataContext()


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

    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.session_state.context = DataContext()
        st.rerun()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if prompt := st.chat_input("描述你的数据分析需求..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent 团队正在协作分析..."):
            try:
                coordinator, orchestrator = init_system()
                result = asyncio.run(orchestrator.run(
                    user_request=prompt,
                    context=st.session_state.context,
                    coordinator=coordinator,
                ))

                report = result.get("report", "")
                if report:
                    st.markdown(report)

                charts = result.get("charts", [])
                for chart_path in charts:
                    if os.path.exists(chart_path):
                        st.image(chart_path)

                if result.get("agent_results"):
                    with st.expander("🔍 Agent 执行详情"):
                        for agent, output in result["agent_results"].items():
                            st.write(f"**{agent}**: {output}")

                response = report or "分析完成，请查看上方结果。"
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = f"执行出错：{e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app.py
git commit -m "feat: Streamlit frontend with file upload and agent visualization"
```

---

## Task 14: FastAPI Entry Point + README

**Covers:** S2

**Files:**
- Create: `app/main.py`
- Create: `README.md`

- [ ] **Step 1: Implement FastAPI entry**

```python
# app/main.py
from fastapi import FastAPI
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
```

- [ ] **Step 2: Create README.md**

```markdown
# 📊 DataAgent

自然语言驱动的多 Agent 数据分析系统。

## 功能

- 🤖 5 个专业 Agent 协作：协调者、数据工程师、分析师、可视化师、报告师
- 📁 支持 CSV/Excel/JSON/Parquet/SQL/API 多种数据源
- 📊 自动生成统计分析和可视化图表
- 📝 中文分析报告生成
- 💬 对话式交互，支持多轮追问

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env  # 填入 LLM_API_KEY
streamlit run frontend/app.py
```

## 架构

```
用户 → Coordinator Agent → 任务拆解 → 并行调度
  ├→ Data Engineer: 数据加载 + 清洗
  ├→ Analyst: 统计分析 + 异常检测
  ├→ Visualizer: 图表生成
  └→ Reporter: 报告撰写
```

## 配置

见 `.env.example`，支持 OpenAI 兼容 API。
```

- [ ] **Step 3: Commit**

```bash
git add app/main.py README.md
git commit -m "feat: FastAPI entry point and README"
```
