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
