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

if "language" not in st.session_state:
    st.session_state.language = FrontendLanguage.CHINESE
set_language(st.session_state.language)

st.title(t("app_title"))


@st.cache_resource
def init_system():
    return create_system()


if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = DataContext()


with st.sidebar:
    st.header(t("settings"))

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

    if st.session_state.context.list_dataframes():
        st.header(t("datasets"))
        for name in st.session_state.context.list_dataframes():
            df = st.session_state.context.get_dataframe(name)
            st.write(t("dataset_info", name=name, rows=len(df), columns=len(df.columns)))

    st.header(t("history"))
    if st.button(t("view_history")):
        from app.history import HistoryManager
        history = HistoryManager(db_path=get_settings().history_db_path)
        sessions = history.get_sessions(limit=10)
        for session in sessions:
            with st.expander(f"{session['created_at']} - {session['status']}"):
                st.write(f"**Request**: {session['user_request']}")
                if session['result']:
                    st.write(f"**Result**: {session['result'][:200]}...")

    if st.button(t("clear_chat")):
        st.session_state.messages = []
        st.session_state.context = DataContext()
        st.rerun()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


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
                            st.write(f"**{artifact['kind']} - {artifact['title']}**")
                            st.write(artifact["summary"])

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
                            st.write(f"**{agent}**: {output}")

                response = report or (t("analysis_failed", errors=error_summary) if result.get("status") == "failed" and errors else t("analysis_completed"))
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = t("error_occurred", error=str(e))
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
