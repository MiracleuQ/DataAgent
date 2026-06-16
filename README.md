# 📊 DataAgent

基于多 Agent 协作的自然语言驱动数据分析系统。

## 核心特性

- 🤖 **6 Agent 协作架构**：协调者（Coordinator）、数据工程师（Data Engineer）、分析师（Analyst）、可视化师（Visualizer）、报告师（Reporter）、审阅者（Reviewer），基于 DAG 依赖图的并行调度引擎
- 📁 **多源数据接入**：支持 CSV/Excel/JSON/Parquet/SQL/API 六种数据源，内置文件沙箱与安全校验
- 📊 **智能可视化**：折线图/柱状图/散点图/饼图自动选型，LLM 驱动图表生成
- 🔍 **自动 EDA**：缺失值/异常值/相关性/高基数偏斜自动检测，生成结构化 Artifact
- 📝 **中文报告生成**：关键发现提炼 + 可操作建议，Reviewer Agent 质量审阅
- 🔄 **增量更新**：数据上下文支持多轮追问与增量分析
- 🌐 **中英双语**：所有 Agent 提示词与前端 UI 支持中英文切换

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 文件上传  │  │ 对话输入  │  │ 图表展示  │  │ 历史记录  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI + WebSocket                        │
│  /api/v1/analyze  │  /ws/analyze/{id}  │  /metrics          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator Engine                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ DAG 调度器    │  │ 消息总线      │  │ 执行追踪      │      │
│  │ (并行执行)    │  │ (pub/sub)    │  │ (事件记录)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Agent 1    │    │   Agent 2    │    │   Agent N    │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
│ │ LLM Chat │ │    │ │ LLM Chat │ │    │ │ LLM Chat │ │
│ │ Tool Loop│ │    │ │ Tool Loop│ │    │ │ Tool Loop│ │
│ └──────────┘ │    │ └──────────┘ │    │ └──────────┘ │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
│ │ 工具注册表│ │    │ │ 工具注册表│ │    │ │ 工具注册表│ │
│ └──────────┘ │    │ └──────────┘ │    │ └──────────┘ │
└──────────────┘    └──────────────┘    └──────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Shared DataContext                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │DataFrames│  │ 分析结果  │  │  图表路径 │  │ Artifacts│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Agent 协作流程

```
用户输入 → Coordinator Agent（任务拆解 + DAG 编排）
              │
              ├─→ Data Engineer Agent（数据加载 + 清洗 + 存入 Context）
              │       │
              │       ▼
              ├─→ Analyst Agent（统计分析 + 异常检测 + 存入 Context）
              │       │
              │       ▼
              ├─→ Visualizer Agent（图表生成 + 存入 Context）
              │       │
              │       ▼
              └─→ Reporter Agent（报告撰写 + 存入 Context）
                      │
                      ▼
                  Reviewer Agent（质量审阅 + 改进建议）
```

## 快速开始

### 环境要求

- Python 3.10+
- OpenAI 兼容 API Key

### 安装

```bash
git clone https://github.com/your-org/DataAgent.git
cd DataAgent
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

### 启动

**Streamlit 前端（推荐）**

```bash
streamlit run frontend/app.py
```

**FastAPI 服务**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

## API 接口

### 分析接口

```bash
POST /api/v1/analyze
Content-Type: application/json

{
  "query": "分析这份销售数据的趋势和异常"
}
```

### 文件上传

```bash
POST /api/v1/upload
Content-Type: multipart/form-data

file: sales_data.csv
```

### WebSocket 实时进度

```bash
ws://localhost:8000/ws/analyze/{client_id}
```

### 监控指标

```bash
GET /metrics          # Prometheus 格式
GET /metrics/json     # JSON 格式
```

## 项目结构

```
DataAgent/
├── app/
│   ├── agents/              # Agent 实现
│   │   ├── base.py          # 基类（超时、状态、消息总线）
│   │   ├── coordinator.py   # 协调者（任务拆解 + DAG 编排）
│   │   ├── data_engineer.py # 数据工程师（加载 + 清洗）
│   │   ├── analyst.py       # 分析师（统计 + 异常检测）
│   │   ├── visualizer.py    # 可视化师（图表生成）
│   │   ├── reporter.py      # 报告师（报告撰写）
│   │   ├── reviewer.py      # 审阅者（质量审阅）
│   │   └── tool_loop.py     # 工具循环（支持并行执行）
│   ├── api/                 # API 层
│   │   ├── routes.py        # REST 接口
│   │   └── websocket.py     # WebSocket 接口
│   ├── core/                # 核心模块
│   │   ├── orchestrator.py  # DAG 调度引擎
│   │   ├── bus.py           # 消息总线（pub/sub）
│   │   ├── context.py       # 共享数据上下文
│   │   ├── sandbox.py       # 代码沙箱（安全隔离）
│   │   ├── artifacts.py     # 制品管理
│   │   └── eda.py           # 自动 EDA
│   ├── tools/               # 工具注册表
│   │   ├── data_tools.py    # 数据工具（加载/清洗/导出）
│   │   ├── analysis_tools.py# 分析工具（统计/聚合/相关性）
│   │   ├── chart_tools.py   # 图表工具（折线/柱状/散点/饼图）
│   │   ├── export_tools.py  # 导出工具（Excel/CSV/JSON/MD/Parquet）
│   │   └── registry.py      # 工具注册中心
│   ├── llm/
│   │   └── client.py        # LLM 客户端（重试 + 缓存）
│   ├── utils/
│   │   ├── cache.py         # 数据缓存（LRU + TTL）
│   │   ├── language.py      # 中英双语提示词
│   │   ├── logger.py        # 日志管理
│   │   └── metrics.py       # Prometheus 指标
│   ├── history/
│   │   └── __init__.py      # SQLite 历史记录
│   ├── config.py            # 配置管理（含启动校验）
│   └── main.py              # FastAPI 入口
├── frontend/
│   ├── app.py               # Streamlit 前端
│   └── i18n.py              # 国际化
├── tests/                   # 测试套件（41 个测试）
├── data/                    # 数据目录
├── docs/                    # 文档
├── requirements.txt         # 依赖
└── .env.example             # 环境变量模板
```

## 技术栈

| 类别 | 技术 |
|------|------|
| **LLM** | OpenAI API（兼容 API） |
| **Agent 框架** | 自研多 Agent 协作系统 |
| **后端** | FastAPI + Uvicorn |
| **前端** | Streamlit |
| **数据处理** | Pandas + NumPy |
| **统计分析** | SciPy + scikit-learn |
| **可视化** | Matplotlib + Plotly |
| **数据库** | SQLite（历史记录） |
| **异步** | asyncio + ThreadPoolExecutor |

## 核心设计

### 1. DAG 调度引擎

Orchestrator 基于有向无环图（DAG）进行任务调度：
- 自动检测依赖关系，最大化并行执行
- 依赖失败时自动跳过下游任务
- 支持超时控制与执行事件追踪

### 2. 消息总线

MessageBus 实现 Agent 间通信：
- 支持点对点消息与广播
- 支持订阅机制（pub/sub）
- 支持超时接收（receive_with_timeout）

### 3. 工具循环

tool_loop 实现 LLM 与工具的多轮交互：
- 只读工具自动并行执行（ThreadPoolExecutor）
- 非只读工具串行执行，确保数据一致性
- 支持多轮工具调用直到 LLM 返回最终结果

### 4. 安全沙箱

Sandbox 隔离执行用户代码：
- 白名单 Builtins 限制
- 危险模块黑名单（os/sys/subprocess 等）
- 进程级隔离 + 超时终止

### 5. 多级缓存

- **LLM 响应缓存**：temperature=0 时自动缓存，TTL 30 分钟
- **数据缓存**：基于内容哈希的 DataFrame 缓存，LRU 淘汰
- **工具结果缓存**：避免重复计算

## 配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_API_KEY` | - | LLM API 密钥（必填） |
| `LLM_BASE_URL` | https://api.openai.com/v1 | API 端点 |
| `LLM_MODEL` | gpt-4o-mini | 模型名称 |
| `LLM_TIMEOUT_SEC` | 60 | LLM 超时（秒） |
| `SANDBOX_TIMEOUT_SEC` | 30 | 沙箱超时（秒） |
| `HISTORY_DB_PATH` | data/history.db | 历史记录路径 |
| `CHART_OUTPUT_DIR` | data/charts | 图表输出目录 |

## 测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_agents.py -v
pytest tests/test_safety_regressions.py -v
```

## License

MIT
