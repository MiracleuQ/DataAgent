import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from app.config import get_settings
from app.core.context import DataContext
from app.factory import create_system
from frontend.i18n import FrontendLanguage, get_i18n, set_language, t


st.set_page_config(page_title="DataAgent", page_icon="✦", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: #0f172a;
        font-family: 'Inter', sans-serif;
    }
    
    .block-container { padding-top: 1.5rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    
    header[data-testid="stHeader"] { background: transparent; }
    
    [data-testid="stSidebar"] { background: #1e293b; border-right: 1px solid #334155; }
    
    h1, h2, h3, h4, h5, h6 { color: #f8fafc !important; }
    
    .stButton > button {
        background: #334155;
        color: #f8fafc;
        border: 1px solid #475569;
        border-radius: 8px;
    }
    .stButton > button:hover { background: #475569; border-color: #6366f1; }
    
    [data-testid="stChatMessage"] { background: #1e293b; border: 1px solid #334155; border-radius: 12px; }
    [data-testid="stChatMessage"][aria-label="user"] { background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.3); }
    
    .stTextInput > div > div > input { background: #1e293b; border: 1px solid #475569; border-radius: 8px; color: #f8fafc; }
    .stTextInput > div > div > input:focus { border-color: #6366f1; }
    
    .stSuccess { background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); color: #4ade80; }
    .stError { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; }
    .stExpander { background: #1e293b; border: 1px solid #334155; border-radius: 8px; }
    
    hr { border: none; height: 1px; background: #334155; margin: 0.75rem 0; }
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
    
    .stMarkdown p { color: #e2e8f0; line-height: 1.7; }
    .stMarkdown strong { color: #ffffff !important; }
    .stMarkdown li { color: #e2e8f0; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #ffffff !important; }
    [data-testid="stChatMessage"] p { color: #e2e8f0; }
    [data-testid="stChatMessage"] li { color: #e2e8f0; }
    
    /* Table styling */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    [data-testid="stDataFrame"] th { background: #334155 !important; color: #f8fafc !important; }
    [data-testid="stDataFrame"] td { background: #1e293b !important; color: #e2e8f0 !important; }
    
    table { border-color: #475569 !important; }
    th { background: #334155 !important; color: #f8fafc !important; }
    td { background: #1e293b !important; color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)


if "language" not in st.session_state:
    st.session_state.language = FrontendLanguage.CHINESE
set_language(st.session_state.language)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = DataContext()
if "input_prompt" not in st.session_state:
    st.session_state.input_prompt = ""


@st.cache_resource
def init_system():
    return create_system()


# Header
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;padding:0 0 12px 0;border-bottom:1px solid #334155;margin-bottom:12px;">
    <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-size:1rem;">✦</div>
    <div>
        <div style="font-size:1.25rem;font-weight:700;color:#f8fafc;">DataAgent</div>
        <div style="font-size:0.75rem;color:#94a3b8;">AI-Powered Data Analysis</div>
    </div>
</div>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown(f'<p style="color:#94a3b8;font-size:0.7rem;letter-spacing:1px;margin-bottom:8px;">{t("language").upper()}</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("chinese"), key="lang_zh", use_container_width=True):
            st.session_state.language = FrontendLanguage.CHINESE
            set_language(FrontendLanguage.CHINESE)
            st.rerun()
    with c2:
        if st.button(t("english"), key="lang_en", use_container_width=True):
            st.session_state.language = FrontendLanguage.ENGLISH
            set_language(FrontendLanguage.ENGLISH)
            st.rerun()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f'<p style="color:#94a3b8;font-size:0.7rem;letter-spacing:1px;margin-bottom:8px;">UPLOAD</p>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose file", type=["csv", "xlsx", "json", "parquet"], label_visibility="collapsed")
    
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
            st.session_state.context.add_dataframe(name, df, auto_profile=True)
            st.success(t("upload_success", filename=uploaded_file.name, rows=len(df)))
        except Exception as e:
            st.error(t("upload_error", error=str(e)))
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if st.session_state.context.list_dataframes():
        st.markdown(f'<p style="color:#94a3b8;font-size:0.7rem;letter-spacing:1px;margin-bottom:8px;">DATASETS</p>', unsafe_allow_html=True)
        for name in st.session_state.context.list_dataframes():
            df = st.session_state.context.get_dataframe(name)
            st.markdown(f'<div style="background:#334155;border:1px solid #475569;border-radius:6px;padding:8px;margin-bottom:4px;"><div style="display:flex;align-items:center;gap:6px;"><div style="width:6px;height:6px;background:#4ade80;border-radius:50%;"></div><span style="color:#f8fafc;font-size:0.85rem;font-weight:500;">{name}</span></div><span style="color:#94a3b8;font-size:0.75rem;">{len(df)} rows</span></div>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if st.button(t("view_history"), use_container_width=True):
        from app.history import HistoryManager
        history = HistoryManager(db_path=get_settings().history_db_path)
        sessions = history.get_sessions(limit=10)
        for session in sessions:
            with st.expander(f"{session['created_at']} - {session['status']}"):
                st.write(f"**Request**: {session['user_request']}")
                if session['result']:
                    st.write(f"**Result**: {session['result'][:200]}...")
    
    if st.button(t("clear_chat"), use_container_width=True):
        st.session_state.messages = []
        st.session_state.context = DataContext()
        st.rerun()


# Welcome section
if not st.session_state.messages:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid #334155;border-radius:16px;padding:1.5rem;margin-bottom:1rem;">
        <h2 style="font-size:1.4rem;font-weight:700;color:#f8fafc;margin-bottom:8px;">{t("welcome_title")}</h2>
        <p style="color:#94a3b8;margin-bottom:16px;font-size:0.9rem;line-height:1.6;">{t("welcome_desc")}</p>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
            <div style="background:#334155;border:1px solid #475569;border-radius:10px;padding:12px;">
                <div style="font-size:1.2rem;margin-bottom:8px;">📊</div>
                <div style="font-size:0.85rem;font-weight:600;color:#f8fafc;margin-bottom:2px;">{t("feature_analysis")}</div>
                <div style="font-size:0.75rem;color:#94a3b8;">{t("feature_analysis_desc")}</div>
            </div>
            <div style="background:#334155;border:1px solid #475569;border-radius:10px;padding:12px;">
                <div style="font-size:1.2rem;margin-bottom:8px;">📈</div>
                <div style="font-size:0.85rem;font-weight:600;color:#f8fafc;margin-bottom:2px;">{t("feature_viz")}</div>
                <div style="font-size:0.75rem;color:#94a3b8;">{t("feature_viz_desc")}</div>
            </div>
            <div style="background:#334155;border:1px solid #475569;border-radius:10px;padding:12px;">
                <div style="font-size:1.2rem;margin-bottom:8px;">📋</div>
                <div style="font-size:0.85rem;font-weight:600;color:#f8fafc;margin-bottom:2px;">{t("feature_report")}</div>
                <div style="font-size:0.75rem;color:#94a3b8;">{t("feature_report_desc")}</div>
            </div>
            <div style="background:#334155;border:1px solid #475569;border-radius:10px;padding:12px;">
                <div style="font-size:1.2rem;margin-bottom:8px;">🔍</div>
                <div style="font-size:0.85rem;font-weight:600;color:#f8fafc;margin-bottom:2px;">{t("feature_anomaly")}</div>
                <div style="font-size:0.75rem;color:#94a3b8;">{t("feature_anomaly_desc")}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div style="font-size:0.95rem;font-weight:600;color:#f8fafc;margin-bottom:10px;">{t("try_asking")}</div>', unsafe_allow_html=True)
    
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button(t("ask_trend"), key="q1", use_container_width=True):
            st.session_state.input_prompt = t("ask_trend")
            st.rerun()
    with q2:
        if st.button(t("ask_top"), key="q2", use_container_width=True):
            st.session_state.input_prompt = t("ask_top")
            st.rerun()
    with q3:
        if st.button(t("ask_anomaly"), key="q3", use_container_width=True):
            st.session_state.input_prompt = t("ask_anomaly")
            st.rerun()
    with q4:
        if st.button(t("ask_report"), key="q4", use_container_width=True):
            st.session_state.input_prompt = t("ask_report")
            st.rerun()


# Chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# Get prompt from quick buttons or chat input
prompt = st.session_state.get("input_prompt", "")
if prompt:
    st.session_state.input_prompt = ""
else:
    prompt = st.chat_input(t("chat_placeholder"))


# Process prompt
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner(t("analyzing")):
            try:
                coordinator, orchestrator = init_system()
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                
                if loop and loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = pool.submit(
                            asyncio.run,
                            orchestrator.run(user_request=prompt, context=st.session_state.context, coordinator=coordinator),
                        ).result()
                else:
                    result = asyncio.run(orchestrator.run(user_request=prompt, context=st.session_state.context, coordinator=coordinator))
                
                report = result.get("report", "")
                if report:
                    st.markdown(report)
                
                review = result.get("review", "")
                if review:
                    with st.expander(t("review")):
                        st.markdown(review)
                
                artifacts = result.get("artifacts", [])
                if artifacts:
                    with st.expander(t("artifacts")):
                        for artifact in artifacts:
                            st.markdown(f"**{artifact['kind']}** - {artifact['title']}\n\n{artifact['summary']}")
                
                errors = result.get("errors", {})
                if result.get("status") == "failed" and errors:
                    error_summary = "\n".join(f"- {agent}: {error}" for agent, error in errors.items() if error)
                    st.error(t("analysis_failed", errors=error_summary))
                
                charts = result.get("charts", [])
                for chart_path in charts:
                    if os.path.exists(chart_path):
                        st.image(chart_path, use_container_width=True)
                
                if result.get("agent_results"):
                    with st.expander(t("agent_details")):
                        for agent, output in result["agent_results"].items():
                            st.markdown(f"**{agent}**\n\n{output}")
                
                response = report or (t("analysis_failed", errors=error_summary) if result.get("status") == "failed" and errors else t("analysis_completed"))
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            except Exception as e:
                error_msg = t("error_occurred", error=str(e))
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
