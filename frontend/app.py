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


st.set_page_config(page_title="DataAgent", page_icon="📊", layout="wide")

# Custom CSS for distinctive styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-card: #1a1a25;
        --accent-1: #6366f1;
        --accent-2: #8b5cf6;
        --accent-3: #a78bfa;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border: #2d2d3d;
        --glow: rgba(99, 102, 241, 0.15);
    }
    
    .stApp {
        background: var(--bg-primary);
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .stApp > header {
        background: transparent !important;
    }
    
    .main .block-container {
        padding-top: 2rem;
        max-width: 100%;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }
    
    /* Chat styling */
    .stChatMessage {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    [data-testid="stChatMessage"][aria-label="user"] {
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
        border: none;
    }
    
    [data-testid="stChatMessage"][aria-label="assistant"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
        color: var(--text-primary);
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-1);
        box-shadow: 0 0 0 2px var(--glow);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px var(--glow);
    }
    
    /* Card styling */
    .stExpander {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 8px;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 8px;
    }
    
    /* Header styling */
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--text-primary) !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-secondary);
        border-radius: 8px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 6px;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent-1);
        color: white;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
</style>
""", unsafe_allow_html=True)


if "language" not in st.session_state:
    st.session_state.language = FrontendLanguage.CHINESE
set_language(st.session_state.language)


# Header with gradient text
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="font-size: 3rem; font-weight: 700; background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;">
        DataAgent
    </h1>
    <p style="color: var(--text-secondary); font-size: 1.1rem; font-weight: 300;">
        AI-Powered Data Analysis Platform
    </p>
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
    # Language selector
    st.markdown("""
    <div style="padding: 1rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1rem;">
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem;">Language</p>
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
    
    st.markdown("---")
    
    # File upload
    st.markdown("""
    <div style="padding: 1rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1rem;">
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem;">📁 Data Upload</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(t("upload_file"), type=["csv", "xlsx", "json", "parquet"])
    
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
    
    st.markdown("---")
    
    # Datasets
    if st.session_state.context.list_dataframes():
        st.markdown("""
        <div style="padding: 1rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1rem;">
            <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem;">📊 Datasets</p>
        </div>
        """, unsafe_allow_html=True)
        
        for name in st.session_state.context.list_dataframes():
            df = st.session_state.context.get_dataframe(name)
            st.markdown(f"""
            <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                <p style="color: var(--text-primary); font-weight: 500; margin-bottom: 0.25rem;">{name}</p>
                <p style="color: var(--text-muted); font-size: 0.85rem;">{len(df)} rows × {len(df.columns)} cols</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # History
    st.markdown("""
    <div style="padding: 1rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1rem;">
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem;">📜 History</p>
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
    
    st.markdown("---")
    
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
                            <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                                <p style="color: var(--accent-3); font-weight: 500; margin-bottom: 0.25rem;">{artifact['kind']} - {artifact['title']}</p>
                                <p style="color: var(--text-secondary);">{artifact['summary']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                
                errors = result.get("errors", {})
                if result.get("status") == "failed" and errors:
                    error_summary = "\n".join(f"- {agent}: {error}" for agent, error in errors.items() if error)
                    st.error(t("analysis_failed", errors=error_summary))
                
                charts = result.get("charts", [])
                for chart_path in charts:
                    if os.path.exists(chart_path):
                        st.image(chart_path)
                
                if result.get("agent_results"):
                    with st.expander(t("agent_details")):
                        for agent, output in result["agent_results"].items():
                            st.markdown(f"""
                            <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                                <p style="color: var(--accent-3); font-weight: 500; margin-bottom: 0.25rem;">{agent}</p>
                                <p style="color: var(--text-secondary);">{output}</p>
                            </div>
                            """, unsafe_allow_html=True)
                
                response = report or (t("analysis_failed", errors=error_summary) if result.get("status") == "failed" and errors else t("analysis_completed"))
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            except Exception as e:
                error_msg = t("error_occurred", error=str(e))
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
