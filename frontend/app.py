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

    :root {
        --bg: #0b1120;
        --panel: #111827;
        --panel-2: #172033;
        --panel-3: #202b3f;
        --line: #2e3a4f;
        --text: #eef2f8;
        --muted: #9ca8ba;
        --soft: #c6d1df;
        --accent: #38bdf8;
        --accent-2: #22c55e;
        --warn: #f59e0b;
    }
    
    .stApp {
        background: var(--bg);
        font-family: 'Inter', sans-serif;
    }
    
    .block-container {
        padding-top: 1.25rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 5.5rem !important;
        max-width: 100% !important;
    }
    
    header[data-testid="stHeader"] { background: transparent; }
    
    [data-testid="stSidebar"] {
        background: #172033;
        border-right: 1px solid var(--line);
    }
    
    h1, h2, h3, h4, h5, h6 { color: var(--text) !important; letter-spacing: 0 !important; }
    
    .stButton > button {
        background: #243149;
        color: var(--text);
        border: 1px solid #37445a;
        border-radius: 8px;
        min-height: 2.5rem;
        font-weight: 600;
    }
    .stButton > button:hover { background: #2d3b55; border-color: var(--accent); color: #ffffff; }
    
    [data-testid="stChatMessage"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: none;
    }
    [data-testid="stChatMessage"][aria-label="user"] {
        background: #142033;
        border-color: #30516c;
    }
    
    .stTextInput > div > div > input {
        background: #111827;
        border: 1px solid var(--line);
        border-radius: 8px;
        color: var(--text);
    }
    .stTextInput > div > div > input:focus { border-color: var(--accent); }
    
    .stSuccess { background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); color: #4ade80; }
    .stError { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; }
    .stExpander {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
    }
    
    hr { border: none; height: 1px; background: var(--line); margin: 0.85rem 0; }
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
    
    .stMarkdown p { color: #d8e0eb; line-height: 1.65; }
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

    .app-shell {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0 0 1rem 0;
        border-bottom: 1px solid var(--line);
        width: min(100%, calc(100vw - 25rem));
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .brand-mark {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        background: #172033;
        border: 1px solid #35546a;
        color: var(--accent);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
    }

    .brand-title { font-size: 1.1rem; font-weight: 750; color: var(--text); }
    .brand-subtitle { color: var(--muted); font-size: 0.78rem; margin-top: 2px; }

    .status-strip {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .status-pill {
        border: 1px solid var(--line);
        background: var(--panel);
        color: var(--soft);
        border-radius: 999px;
        padding: 0.42rem 0.68rem;
        font-size: 0.78rem;
        white-space: nowrap;
    }

    .workbench {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 1rem;
    }

    .section-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem;
        width: min(100%, calc(100vw - 25rem));
        overflow: hidden;
    }

    .section-title {
        color: var(--text);
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 0.25rem;
    }

    .section-caption {
        color: var(--muted);
        font-size: 0.84rem;
        margin-bottom: 0.9rem;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.75rem;
    }

    .metric-card {
        background: var(--panel-2);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.85rem;
        min-height: 86px;
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .metric-value {
        color: var(--text);
        font-size: 1.45rem;
        font-weight: 760;
        margin-top: 0.35rem;
    }

    .metric-note {
        color: var(--muted);
        font-size: 0.76rem;
        margin-top: 0.2rem;
        overflow-wrap: anywhere;
    }

    .template-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.75rem;
    }

    .dataset-card {
        background: #202b3f;
        border: 1px solid #33445f;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.45rem;
    }

    .dataset-name {
        color: var(--text);
        font-size: 0.88rem;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    .dataset-meta {
        color: var(--muted);
        font-size: 0.76rem;
        margin-top: 0.22rem;
    }

    .side-label {
        color: var(--muted);
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.55rem;
    }

    .empty-note {
        color: var(--muted);
        background: #111827;
        border: 1px dashed #3b4658;
        border-radius: 8px;
        padding: 0.85rem;
        font-size: 0.84rem;
    }

    .result-toolbar {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin: 0.5rem 0 1rem 0;
    }

    @media (max-width: 900px) {
        .topbar, .section-panel { width: 100%; }
        .topbar { align-items: flex-start; flex-direction: column; }
        .status-strip { justify-content: flex-start; }
        .metric-grid, .template-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }

    @media (max-width: 560px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        .metric-grid, .template-grid { grid-template-columns: 1fr; }
    }
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


def init_system():
    return create_system()


def dataset_stats(context: DataContext) -> dict:
    names = context.list_dataframes()
    rows = 0
    columns = 0
    latest = t("no_dataset")
    if names:
        latest = names[-1]
        for name in names:
            df = context.get_dataframe(name)
            if df is not None:
                rows += len(df)
                columns += len(df.columns)
    return {
        "count": len(names),
        "rows": rows,
        "columns": columns,
        "latest": latest,
    }


def render_topbar(context: DataContext) -> None:
    stats = dataset_stats(context)
    data_status = t("status_ready") if stats["count"] else t("status_waiting")
    st.markdown(
        f"""
        <div class="topbar">
            <div class="brand">
                <div class="brand-mark">DA</div>
                <div>
                    <div class="brand-title">DataAgent</div>
                    <div class="brand-subtitle">{t("brand_subtitle")}</div>
                </div>
            </div>
            <div class="status-strip">
                <div class="status-pill">{t("status_label")}: {data_status}</div>
                <div class="status-pill">{t("metric_datasets")}: {stats["count"]}</div>
                <div class="status-pill">{t("rows_label")}: {stats["rows"]:,}</div>
                <div class="status-pill">{t("latest_label")}: {stats["latest"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_panel(context: DataContext) -> None:
    stats = dataset_stats(context)
    chart_count = len(context.charts)
    artifact_count = len(context.artifacts)
    result_count = len(context.analysis_results)
    latest_note = stats["latest"] if stats["count"] else t("metric_upload_note")
    st.markdown(
        f"""
        <div class="section-panel">
            <div class="section-title">{t("workspace_title")}</div>
            <div class="section-caption">{t("workspace_desc")}</div>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">{t("metric_datasets")}</div>
                    <div class="metric-value">{stats["count"]}</div>
                    <div class="metric-note">{latest_note}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">{t("metric_rows_loaded")}</div>
                    <div class="metric-value">{stats["rows"]:,}</div>
                    <div class="metric-note">{t("metric_rows_note")}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">{t("metric_outputs")}</div>
                    <div class="metric-value">{chart_count + artifact_count}</div>
                    <div class="metric-note">{t("metric_outputs_note", charts=chart_count, artifacts=artifact_count)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">{t("metric_findings")}</div>
                    <div class="metric-value">{result_count}</div>
                    <div class="metric-note">{t("metric_findings_note")}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dataset_card(name: str, df: pd.DataFrame) -> None:
    missing = int(df.isna().sum().sum())
    st.markdown(
        f"""
        <div class="dataset-card">
            <div class="dataset-name">{name}</div>
            <div class="dataset-meta">{len(df):,} rows · {len(df.columns):,} columns · {missing:,} missing values</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_topbar(st.session_state.context)


with st.sidebar:
    st.markdown(f'<div class="side-label">{t("side_workspace")}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="empty-note">{t("side_workspace_note")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(f'<div class="side-label">{t("language")}</div>', unsafe_allow_html=True)
    
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
    st.markdown(f'<div class="side-label">{t("side_data_source")}</div>', unsafe_allow_html=True)
    
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
        st.markdown(f'<div class="side-label">{t("side_active_datasets")}</div>', unsafe_allow_html=True)
        for name in st.session_state.context.list_dataframes():
            df = st.session_state.context.get_dataframe(name)
            if df is not None:
                render_dataset_card(name, df)
    else:
        st.markdown(f'<div class="side-label">{t("side_active_datasets")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="empty-note">{t("side_no_data")}</div>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f'<div class="side-label">{t("side_session")}</div>', unsafe_allow_html=True)
    
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
    render_metric_panel(st.session_state.context)
    
    st.markdown(
        """
        <div class="section-panel">
            <div class="section-title">{title}</div>
            <div class="section-caption">{desc}</div>
        </div>
        """.format(title=t("templates_title"), desc=t("templates_desc")),
        unsafe_allow_html=True,
    )
    
    q1, q2 = st.columns(2)
    with q1:
        if st.button(t("template_quality"), key="q1", use_container_width=True):
            st.session_state.input_prompt = t("prompt_quality")
            st.rerun()
    with q2:
        if st.button(t("template_trend"), key="q2", use_container_width=True):
            st.session_state.input_prompt = t("prompt_trend")
            st.rerun()
    q3, q4 = st.columns(2)
    with q3:
        if st.button(t("template_anomaly"), key="q3", use_container_width=True):
            st.session_state.input_prompt = t("prompt_anomaly")
            st.rerun()
    with q4:
        if st.button(t("template_report"), key="q4", use_container_width=True):
            st.session_state.input_prompt = t("prompt_report")
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
                review = result.get("review", "")
                artifacts = result.get("artifacts", [])
                errors = result.get("errors", {})
                error_summary = ""
                if result.get("status") == "failed" and errors:
                    error_summary = "\n".join(f"- {agent}: {error}" for agent, error in errors.items() if error)
                    st.error(t("analysis_failed", errors=error_summary))
                
                charts = result.get("charts", [])
                agent_results = result.get("agent_results", {})

                tabs = st.tabs([t("tab_report"), t("tab_charts"), t("tab_review"), t("tab_artifacts"), t("tab_execution")])
                with tabs[0]:
                    if report:
                        st.markdown(report)
                    elif error_summary:
                        st.markdown(error_summary)
                    else:
                        st.info(t("analysis_completed"))

                with tabs[1]:
                    visible_charts = [path for path in charts if os.path.exists(path)]
                    if visible_charts:
                        for chart_path in visible_charts:
                            st.image(chart_path, use_container_width=True)
                    else:
                        st.caption(t("no_charts"))

                with tabs[2]:
                    if review:
                        st.markdown(review)
                    else:
                        st.caption(t("no_review_notes"))

                with tabs[3]:
                    if artifacts:
                        for artifact in artifacts:
                            st.markdown(f"**{artifact['kind']}** - {artifact['title']}\n\n{artifact['summary']}")
                    else:
                        st.caption(t("no_artifacts"))

                with tabs[4]:
                    execution = result.get("execution", {})
                    if execution:
                        c1, c2, c3 = st.columns(3)
                        c1.metric(t("execution_tasks"), execution.get("total_tasks", 0))
                        c2.metric(t("execution_succeeded"), execution.get("succeeded", 0))
                        c3.metric(t("execution_failed"), execution.get("failed", 0))
                    if agent_results:
                        for agent, output in agent_results.items():
                            with st.expander(agent):
                                st.markdown(output)
                    else:
                        st.caption(t("no_execution_details"))
                
                response = report or (t("analysis_failed", errors=error_summary) if result.get("status") == "failed" and errors else t("analysis_completed"))
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            except Exception as e:
                error_msg = t("error_occurred", error=str(e))
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
