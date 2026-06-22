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


st.set_page_config(page_title="DataAgent", page_icon="✨", layout="wide")

# Premium dark theme with distinctive styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-gradient-1: #0f0f1a;
        --bg-gradient-2: #1a1a2e;
        --bg-gradient-3: #16213e;
        --surface-1: #1e1e32;
        --surface-2: #252540;
        --surface-3: #2d2d4a;
        --accent-primary: #ff6b6b;
        --accent-secondary: #4ecdc4;
        --accent-tertiary: #ffe66d;
        --accent-purple: #a855f7;
        --accent-blue: #3b82f6;
        --text-bright: #ffffff;
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-accent: rgba(255, 107, 107, 0.3);
        --shadow-glow: 0 0 40px rgba(255, 107, 107, 0.15);
        --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-gradient-1) 0%, var(--bg-gradient-2) 50%, var(--bg-gradient-3) 100%);
        font-family: 'Outfit', sans-serif;
        color: var(--text-primary);
    }
    
    .stApp > header {
        background: transparent !important;
    }
    
    .main .block-container {
        padding-top: 1rem;
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--surface-1) 0%, var(--surface-2) 100%);
        border-right: 1px solid var(--border-subtle);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-primary) !important;
    }
    
    /* Chat container */
    [data-testid="stChatMessage"] {
        background: rgba(30, 30, 50, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        box-shadow: var(--shadow-card);
        transition: all 0.3s ease;
    }
    
    [data-testid="stChatMessage"]:hover {
        border-color: rgba(255, 255, 255, 0.12);
        transform: translateY(-2px);
    }
    
    [data-testid="stChatMessage"][aria-label="user"] {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(59, 130, 246, 0.3));
        border: 1px solid rgba(168, 85, 247, 0.4);
    }
    
    [data-testid="stChatMessage"][aria-label="assistant"] {
        background: linear-gradient(135deg, rgba(78, 205, 196, 0.15), rgba(255, 107, 107, 0.1));
        border: 1px solid rgba(78, 205, 196, 0.25);
    }
    
    /* Input field */
    .stTextInput > div > div > input {
        background: var(--surface-2);
        border: 2px solid var(--border-subtle);
        border-radius: 12px;
        color: var(--text-bright);
        font-family: 'Outfit', sans-serif;
        font-size: 1rem;
        padding: 1rem 1.25rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-secondary);
        box-shadow: 0 0 0 4px rgba(78, 205, 196, 0.2), var(--shadow-glow);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary), #ff8e8e);
        color: var(--text-bright);
        border: none;
        border-radius: 10px;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Secondary buttons */
    [data-testid="stSidebar"] .stButton > button {
        background: var(--surface-3);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--accent-primary);
    }
    
    /* Expanders */
    .stExpander {
        background: rgba(30, 30, 50, 0.5);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        overflow: hidden;
    }
    
    .stExpander header {
        background: var(--surface-2);
        border-bottom: 1px solid var(--border-subtle);
    }
    
    /* Success/Error */
    .stSuccess {
        background: linear-gradient(135deg, rgba(78, 205, 196, 0.2), rgba(78, 205, 196, 0.1));
        border: 1px solid rgba(78, 205, 196, 0.4);
        border-radius: 10px;
        color: var(--accent-secondary);
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(255, 107, 107, 0.2), rgba(255, 107, 107, 0.1));
        border: 1px solid rgba(255, 107, 107, 0.4);
        border-radius: 10px;
        color: var(--accent-primary);
    }
    
    /* Headings */
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif !important;
        color: var(--text-bright) !important;
        font-weight: 700 !important;
    }
    
    h1 {
        font-size: 3.5rem !important;
        letter-spacing: -1px;
    }
    
    h2 {
        font-size: 2rem !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: var(--surface-1) !important;
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        font-family: 'Space Mono', monospace;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface-1);
        border-radius: 12px;
        padding: 6px;
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 8px;
        font-family: 'Outfit', sans-serif;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
        color: var(--text-bright);
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3);
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-subtle), transparent);
        margin: 1.5rem 0;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--surface-1);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--surface-3);
        border-radius: 5px;
        border: 2px solid var(--surface-1);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-primary);
    }
    
    /* File uploader */
    .stFileUploader {
        background: var(--surface-1);
        border: 2px dashed var(--border-subtle);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: var(--accent-secondary);
        background: rgba(78, 205, 196, 0.05);
    }
    
    /* Markdown content */
    .stMarkdown {
        line-height: 1.7;
    }
    
    .stMarkdown p {
        color: var(--text-primary);
    }
    
    .stMarkdown strong {
        color: var(--text-bright);
        font-weight: 600;
    }
    
    .stMarkdown code {
        background: var(--surface-2);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-family: 'Space Mono', monospace;
        font-size: 0.9em;
        color: var(--accent-secondary);
    }
    
    /* Animation keyframes */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .stChatMessage {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Spinner */
    .stSpinner {
        color: var(--accent-secondary);
    }
</style>
""", unsafe_allow_html=True)


if "language" not in st.session_state:
    st.session_state.language = FrontendLanguage.CHINESE
set_language(st.session_state.language)


# Elegant header with animated gradient
st.markdown("""
<div style="text-align: center; padding: 3rem 0 2rem 0; position: relative;">
    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 300px; height: 300px; background: radial-gradient(circle, rgba(255,107,107,0.15) 0%, transparent 70%); border-radius: 50%; filter: blur(40px); pointer-events: none;"></div>
    <h1 style="font-size: 4rem; font-weight: 800; background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 50%, #ffe66d 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.75rem; position: relative; letter-spacing: -2px;">
        DataAgent
    </h1>
    <p style="color: var(--text-secondary); font-size: 1.2rem; font-weight: 300; letter-spacing: 3px; text-transform: uppercase; position: relative;">
        Intelligent Data Analysis
    </p>
    <div style="width: 60px; height: 3px; background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)); margin: 1.5rem auto 0; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)


@st.cache_resource
def init_system():
    return create_system()


if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = DataContext()


with st.sidebar:
    # Logo/Brand
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0 2rem 0; border-bottom: 1px solid var(--border-subtle); margin-bottom: 1.5rem;">
        <div style="width: 50px; height: 50px; background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.75rem; font-size: 1.5rem; box-shadow: 0 4px 20px rgba(255, 107, 107, 0.3);">
            ✦
        </div>
        <p style="color: var(--text-muted); font-size: 0.75rem; letter-spacing: 2px; text-transform: uppercase;">Control Panel</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Language selector
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <p style="color: var(--text-muted); font-size: 0.7rem; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 0.75rem;">🌐 Language</p>
    </div>
    """, unsafe_allow_html=True)
    
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        if st.button("中文", use_container_width=True):
            st.session_state.language = FrontendLanguage.CHINESE
            set_language(FrontendLanguage.CHINESE)
            st.rerun()
    with lang_col2:
        if st.button("English", use_container_width=True):
            st.session_state.language = FrontendLanguage.ENGLISH
            set_language(FrontendLanguage.ENGLISH)
            st.rerun()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # File upload
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <p style="color: var(--text-muted); font-size: 0.7rem; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 0.75rem;">📁 Upload Data</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=["csv", "xlsx", "json", "parquet"], label_visibility="collapsed")
    
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
    
    # Datasets
    if st.session_state.context.list_dataframes():
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <p style="color: var(--text-muted); font-size: 0.7rem; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 0.75rem;">📊 Datasets</p>
        </div>
        """, unsafe_allow_html=True)
        
        for name in st.session_state.context.list_dataframes():
            df = st.session_state.context.get_dataframe(name)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, var(--surface-2), var(--surface-3)); border: 1px solid var(--border-subtle); border-radius: 10px; padding: 1rem; margin: 0.5rem 0; transition: all 0.3s ease;">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <div style="width: 8px; height: 8px; background: var(--accent-secondary); border-radius: 50%;"></div>
                    <p style="color: var(--text-bright); font-weight: 600; margin: 0; font-size: 0.9rem;">{name}</p>
                </div>
                <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0;">{len(df)} rows × {len(df.columns)} cols</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # History
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <p style="color: var(--text-muted); font-size: 0.7rem; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 0.75rem;">📜 History</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(t("view_history"), use_container_width=True):
        from app.history import HistoryManager
        history = HistoryManager(db_path=get_settings().history_db_path)
        sessions = history.get_sessions(limit=10)
        for session in sessions:
            with st.expander(f"{session['created_at']} - {session['status']}"):
                st.write(f"**Request**: {session['user_request']}")
                if session['result']:
                    st.write(f"**Result**: {session['result'][:200]}...")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Clear chat
    if st.button(t("clear_chat"), use_container_width=True):
        st.session_state.messages = []
        st.session_state.context = DataContext()
        st.rerun()


# Chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# Chat input
if prompt := st.chat_input(t("chat_placeholder")):
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
                            orchestrator.run(
                                user_request=prompt,
                                context=st.session_state.context,
                                coordinator=coordinator,
                            ),
                        ).result()
                else:
                    result = asyncio.run(orchestrator.run(
                        user_request=prompt,
                        context=st.session_state.context,
                        coordinator=coordinator,
                    ))
                
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
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, var(--surface-2), var(--surface-3)); border: 1px solid var(--border-subtle); border-radius: 10px; padding: 1.25rem; margin: 0.75rem 0; position: relative; overflow: hidden;">
                                <div style="position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: linear-gradient(180deg, var(--accent-primary), var(--accent-secondary));"></div>
                                <div style="padding-left: 1rem;">
                                    <p style="color: var(--accent-tertiary); font-weight: 600; margin-bottom: 0.5rem; font-size: 0.95rem;">{artifact['kind']} — {artifact['title']}</p>
                                    <p style="color: var(--text-secondary); margin: 0; line-height: 1.6;">{artifact['summary']}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                errors = result.get("errors", {})
                if result.get("status") == "failed" and errors:
                    error_summary = "\n".join(f"- {agent}: {error}" for agent, error in errors.items() if error)
                    st.error(t("analysis_failed", errors=error_summary))
                
                charts = result.get("charts", [])
                for chart_path in charts:
                    if os.path.exists(chart_path):
                        st.markdown(f"""
                        <div style="background: var(--surface-1); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1rem; margin: 1rem 0; box-shadow: var(--shadow-card);">
                            <img src="file:///{chart_path}" style="width: 100%; border-radius: 8px;" />
                        </div>
                        """, unsafe_allow_html=True)
                        st.image(chart_path)
                
                if result.get("agent_results"):
                    with st.expander(t("agent_details")):
                        for agent, output in result["agent_results"].items():
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, var(--surface-2), var(--surface-3)); border: 1px solid var(--border-subtle); border-radius: 10px; padding: 1.25rem; margin: 0.75rem 0; position: relative; overflow: hidden;">
                                <div style="position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: var(--accent-purple);"></div>
                                <div style="padding-left: 1rem;">
                                    <p style="color: var(--accent-purple); font-weight: 600; margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">{agent}</p>
                                    <p style="color: var(--text-secondary); margin: 0; line-height: 1.6;">{output}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                response = report or (t("analysis_failed", errors=error_summary) if result.get("status") == "failed" and errors else t("analysis_completed"))
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            except Exception as e:
                error_msg = t("error_occurred", error=str(e))
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
