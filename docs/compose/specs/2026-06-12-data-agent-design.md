# DataAgent — 多 Agent 数据分析系统设计文档

## [S1] 项目定位

自然语言驱动的多 Agent 数据分析系统。用户用中文描述分析需求，多个专业 Agent 自动完成数据采集、清洗、分析、可视化、报告生成全流程。

- **目标用户**：数据分析师、业务人员、开发者
- **核心卖点**：纯 Python 自研 Agent 框架，不依赖 LangChain/AutoGen/CrewAI
- **交付形式**：开源项目，Streamlit Web UI + CLI

## [S2] 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 前端 | Streamlit |
| LLM | OpenAI SDK（兼容任意 OpenAI API） |
| 数据分析 | pandas + NumPy + scipy + sklearn |
| 可视化 | matplotlib（静态）+ plotly（交互式） |
| 对话历史 | SQLite |
| 配置管理 | Pydantic Settings |

## [S3] Agent 架构

### [S3.1] Agent 基类

```python
class BaseAgent(ABC):
    role: str           # 角色名称
    system_prompt: str  # 系统提示词
    tools: list[Tool]   # 可用工具列表
    memory: AgentMemory # 短期记忆

    @abstractmethod
    async def run(self, task: str, context: DataContext) -> AgentResult
```

每个 Agent 通过 `run()` 接收任务，返回结构化结果。Agent 内部用 LLM + function calling 驱动工具调用。

### [S3.2] 五个专业 Agent

| Agent | 职责 | 工具 |
|-------|------|------|
| **Coordinator** | 理解意图，拆分子任务，调度其他 Agent，汇总结果 | plan_tasks, delegate, summarize |
| **Data Engineer** | 读取数据源、清洗缺失值/异常值、类型转换 | read_file, read_sql, call_api, clean_data, transform |
| **Analyst** | 统计分析、聚合、相关性、异常检测、ML 建模 | describe, groupby, correlate, detect_anomaly, train_model |
| **Visualizer** | 生成图表 | plot_line, plot_bar, plot_scatter, plot_heatmap, plot_box |
| **Reporter** | 生成中文洞察报告 | generate_report, format_table |

### [S3.3] 消息总线

```python
class Message:
    sender: str
    receiver: str
    content: str
    msg_type: Literal["task", "result", "error", "info"]
    metadata: dict
```

Agent 之间通过消息总线异步通信，Coordinator 充当调度中心。

### [S3.4] 共享上下文

```python
class DataContext:
    dataframes: dict[str, DataFrame]  # 命名数据集
    analysis_results: dict[str, Any]  # 分析结果
    charts: list[str]                 # 图表文件路径
    metadata: dict                    # 元数据
```

所有 Agent 共享 DataContext，避免数据拷贝。

### [S3.5] 任务规划

Coordinator 将用户需求拆解为 DAG：
```
用户: "分析销售数据，找出 top10 客户，画趋势图"
  → Task1: Data Engineer 读取数据
  → Task2: Analyst 计算 top10（依赖 Task1）
  → Task3: Visualizer 画趋势图（依赖 Task1）
  → Task4: Reporter 生成报告（依赖 Task2, Task3）
```

## [S4] 数据源支持

| 数据源 | 实现方式 |
|--------|----------|
| 本地文件 | CSV/Excel/JSON/Parquet，pandas 直接读取 |
| SQL 数据库 | SQLAlchemy 连接 MySQL/PostgreSQL/SQLite |
| API 接口 | httpx 调用 REST API，自动解析 JSON 响应 |
| 文本输入 | 用户直接粘贴表格数据，pandas 解析 |

Data Engineer Agent 根据用户描述自动选择数据源。

## [S5] 代码沙箱

Analyst Agent 可生成 Python 代码并在沙箱中执行：
- 限制可用模块（pandas, numpy, scipy, sklearn）
- 禁止文件系统写入（除指定输出目录）
- 禁止网络请求（除指定 API）
- 设置执行超时（默认 30s）
- 捕获 stdout/stderr 和异常

## [S6] Streamlit 前端

- 左侧：对话历史 + 新建对话
- 中间：对话界面，支持文件上传
- 右侧：Agent 执行过程可视化（当前执行到哪一步）
- 底部：数据预览 + 图表展示

## [S7] 错误处理

| 场景 | 策略 |
|------|------|
| LLM 调用失败 | 指数退避重试 3 次 |
| Agent 执行异常 | Coordinator 换策略或跳过 |
| 数据源读取失败 | 提示用户检查文件/连接 |
| 代码执行超时 | 终止进程，返回超时提示 |
| 图表生成失败 | 降级为文本描述 |

## [S8] 项目结构

```
DataAgent/
├── app/
│   ├── agents/
│   │   ├── base.py          # Agent 基类
│   │   ├── coordinator.py   # 调度 Agent
│   │   ├── data_engineer.py # 数据工程 Agent
│   │   ├── analyst.py       # 分析 Agent
│   │   ├── visualizer.py    # 可视化 Agent
│   │   └── reporter.py      # 报告 Agent
│   ├── core/
│   │   ├── bus.py           # 消息总线
│   │   ├── context.py       # 共享上下文
│   │   ├── planner.py       # 任务规划器
│   │   ├── sandbox.py       # 代码沙箱
│   │   └── orchestrator.py  # 编排引擎
│   ├── tools/
│   │   ├── data_tools.py    # 数据读写工具
│   │   ├── analysis_tools.py # 分析工具
│   │   ├── chart_tools.py   # 图表工具
│   │   └── registry.py      # 工具注册表
│   ├── llm/
│   │   └── client.py        # LLM 客户端
│   ├── history/
│   │   └── store.py         # 对话历史
│   ├── config.py
│   └── main.py              # FastAPI 入口
├── frontend/
│   └── app.py               # Streamlit 入口
├── tests/
├── docs/
├── .env.example
├── requirements.txt
└── README.md
```
