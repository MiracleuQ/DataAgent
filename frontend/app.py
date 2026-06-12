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
