<div align="center">

# ✦ DataAgent

### AI-Powered Multi-Agent Data Analysis System

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**用自然语言驱动数据分析，让 AI 团队为你工作**

[快速开始](#-快速开始) · [功能特性](#-功能特性) · [系统架构](#-系统架构) · [API 文档](#-api-接口)

</div>

---

## ✨ 功能特性

<table>
<tr>
<td width="50%">

### 🤖 智能 Agent 协作
- **6 个专业 Agent** 组成分析团队
- 基于 DAG 的**并行调度引擎**
- Agent 间通过**消息总线**协作
- 自动依赖分析与任务编排

</td>
<td width="50%">

### 📊 AI 驱动可视化
- **8 种图表类型**：折线/柱状/散点/饼图/热力图/箱线/直方/树状图
- LLM 自动选择最佳图表
- **Plotly** 交互式图表
- 专业的配色与样式

</td>
</tr>
<tr>
<td>

### 🔍 自动化分析
- 自动 **EDA**（探索性数据分析）
- 缺失值/异常值/相关性检测
- 多维度统计分析
- 结构化洞察提取

</td>
<td>

### 🌐 企业级特性
- **中英双语**完整支持
- WebSocket 实时进度
- SQLite 历史记录
- Prometheus 监控指标

</td>
</tr>
</table>

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- OpenAI 兼容 API Key（DeepSeek/OpenAI/其他）

### 安装

```bash
# 克隆项目
git clone https://github.com/MiracleuQ/DataAgent.git
cd DataAgent

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制环境变量模板
cp .env.example .env
```

编辑 `.env` 文件：

```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-v4-pro
```

### 启动

```bash
# 启动 Streamlit 前端（推荐）
streamlit run frontend/app.py

# 或启动 FastAPI 服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 **http://localhost:8501** 开始使用！

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit Frontend                         │
│   📁 Upload  │  💬 Chat  │  📊 Charts  │  📜 History           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Engine                          │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│   │  DAG 调度器  │  │  消息总线    │  │  执行追踪    │           │
│   │  (并行执行)  │  │  (pub/sub)  │  │  (事件记录)  │           │
│   └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   📋 Data     │    │   📊 Analysis │    │   📈 Viz      │
│   Engineer    │───▶│   Analyst     │───▶│   Visualizer  │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Shared DataContext                          │
│   DataFrames  │  Results  │  Charts  │  Artifacts              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📖 Agent 协作流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  🎯 Coordinator Agent                                       │
│  • 理解用户意图                                              │
│  • 拆解分析任务                                              │
│  • 生成 DAG 执行计划                                         │
└─────────────────────────────────────────────────────────────┘
    │
    ├──▶ 📋 Data Engineer Agent
    │    • 加载数据（CSV/Excel/JSON/Parquet/SQL/API）
    │    • 数据清洗与预处理
    │    • 存入 DataContext
    │
    ├──▶ 📊 Analyst Agent
    │    • 统计分析（描述性/分组/相关性）
    │    • 异常值检测
    │    • 存入 DataContext
    │
    ├──▶ 📈 Visualizer Agent
    │    • AI 选择图表类型
    │    • 生成专业图表（Plotly）
    │    • 存入 DataContext
    │
    └──▶ 📝 Reporter Agent
         • 生成分析报告
         • 提炼关键洞察
         • Reviewer Agent 质量审阅
```

---

## 🔌 API 接口

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

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analyze/{client_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data); // 实时分析进度
};
```

### 监控指标

```bash
GET /metrics          # Prometheus 格式
GET /metrics/json     # JSON 格式
```

---

## 📁 项目结构

```
DataAgent/
├── app/
│   ├── agents/              # Agent 实现
│   │   ├── base.py          # 基类（超时、状态、消息总线）
│   │   ├── coordinator.py   # 协调者（任务拆解 + DAG 编排）
│   │   ├── data_engineer.py # 数据工程师（加载 + 清洗）
│   │   ├── analyst.py       # 分析师（统计 + 异常检测）
│   │   ├── visualizer.py    # 可视化师（AI 图表生成）
│   │   ├── reporter.py      # 报告师（报告撰写）
│   │   ├── reviewer.py      # 审阅者（质量审阅）
│   │   └── tool_loop.py     # 工具循环（并行执行）
│   ├── core/                # 核心模块
│   │   ├── orchestrator.py  # DAG 调度引擎
│   │   ├── bus.py           # 消息总线（pub/sub）
│   │   ├── context.py       # 共享数据上下文
│   │   └── sandbox.py       # 代码沙箱（安全隔离）
│   ├── tools/               # 工具注册表
│   │   ├── data_tools.py    # 数据工具
│   │   ├── analysis_tools.py# 分析工具
│   │   ├── chart_tools.py   # 图表工具
│   │   ├── smart_chart_tools.py # AI 图表工具
│   │   └── registry.py      # 工具注册中心
│   └── llm/
│       └── client.py        # LLM 客户端（重试 + 缓存）
├── frontend/
│   ├── app.py               # Streamlit 前端
│   └── i18n.py              # 国际化
├── tests/                   # 测试套件（87+ 测试）
├── requirements.txt         # 依赖
└── .env.example             # 环境变量模板
```

---

## 🛠️ 技术栈

| 类别 | 技术 | 用途 |
|:-----|:-----|:-----|
| **AI/LLM** | DeepSeek / OpenAI API | 智能分析与决策 |
| **Agent 框架** | 自研多 Agent 系统 | 任务协作与调度 |
| **后端** | FastAPI + Uvicorn | REST API 服务 |
| **前端** | Streamlit | 交互式界面 |
| **数据处理** | Pandas + NumPy | 数据清洗与转换 |
| **统计分析** | SciPy + scikit-learn | 统计检验与机器学习 |
| **可视化** | Plotly + Matplotlib | 图表生成 |
| **数据库** | SQLite | 历史记录存储 |
| **异步** | asyncio + ThreadPoolExecutor | 并发任务执行 |

---

## ⚙️ 配置项

| 配置项 | 默认值 | 说明 |
|:-------|:-------|:-----|
| `LLM_API_KEY` | - | LLM API 密钥（必填） |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | API 端点 |
| `LLM_MODEL` | `gpt-4o-mini` | 模型名称 |
| `LLM_TIMEOUT_SEC` | `60` | LLM 超时（秒） |
| `SANDBOX_TIMEOUT_SEC` | `30` | 沙箱超时（秒） |
| `HISTORY_DB_PATH` | `data/history.db` | 历史记录路径 |
| `CHART_OUTPUT_DIR` | `data/charts` | 图表输出目录 |

---

## 🧪 测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_agents.py -v
pytest tests/test_context.py -v
```

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

Made with ❤️ by [MiracleuQ](https://github.com/MiracleuQ)

</div>
