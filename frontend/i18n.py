from enum import Enum
from typing import Dict


class FrontendLanguage(str, Enum):
    CHINESE = "zh"
    ENGLISH = "en"


TRANSLATIONS: Dict[FrontendLanguage, Dict[str, str]] = {
    FrontendLanguage.CHINESE: {
        "app_title": "📊 DataAgent — 多 Agent 数据分析系统",
        "settings": "⚙️ 设置",
        "upload_file": "上传数据文件",
        "upload_success": "已加载 {filename} ({rows} 行)",
        "upload_error": "加载失败：{error}",
        "datasets": "📊 数据集",
        "dataset_info": "**{name}**: {rows} 行 × {columns} 列",
        "history": "📜 历史记录",
        "view_history": "查看历史",
        "clear_chat": "🗑️ 清空对话",
        "chat_placeholder": "描述你的数据分析需求...",
        "analyzing": "Agent 团队正在协作分析...",
        "review": "Review",
        "artifacts": "Artifacts",
        "agent_details": "🔍 Agent 执行详情",
        "analysis_failed": "Analysis failed:\n{errors}",
        "analysis_completed": "Analysis completed.",
        "error_occurred": "执行出错：{error}",
        "export": "导出",
        "export_excel": "导出 Excel",
        "export_csv": "导出 CSV",
        "export_json": "导出 JSON",
        "export_markdown": "导出 Markdown",
        "language": "语言",
        "chinese": "中文",
        "english": "English",
    },
    FrontendLanguage.ENGLISH: {
        "app_title": "📊 DataAgent — Multi-Agent Data Analysis System",
        "settings": "⚙️ Settings",
        "upload_file": "Upload Data File",
        "upload_success": "Loaded {filename} ({rows} rows)",
        "upload_error": "Load failed: {error}",
        "datasets": "📊 Datasets",
        "dataset_info": "**{name}**: {rows} rows × {columns} columns",
        "history": "📜 History",
        "view_history": "View History",
        "clear_chat": "🗑️ Clear Chat",
        "chat_placeholder": "Describe your data analysis needs...",
        "analyzing": "Agent team is analyzing...",
        "review": "Review",
        "artifacts": "Artifacts",
        "agent_details": "🔍 Agent Execution Details",
        "analysis_failed": "Analysis failed:\n{errors}",
        "analysis_completed": "Analysis completed.",
        "error_occurred": "Error occurred: {error}",
        "export": "Export",
        "export_excel": "Export Excel",
        "export_csv": "Export CSV",
        "export_json": "Export JSON",
        "export_markdown": "Export Markdown",
        "language": "Language",
        "chinese": "中文",
        "english": "English",
    },
}


class I18n:
    def __init__(self, language: FrontendLanguage = FrontendLanguage.CHINESE):
        self._language = language

    @property
    def language(self) -> FrontendLanguage:
        return self._language

    @language.setter
    def language(self, value: FrontendLanguage) -> None:
        self._language = value

    def t(self, key: str, **kwargs) -> str:
        translations = TRANSLATIONS.get(self._language, TRANSLATIONS[FrontendLanguage.CHINESE])
        text = translations.get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text


_i18n: I18n = None


def get_i18n() -> I18n:
    global _i18n
    if _i18n is None:
        _i18n = I18n()
    return _i18n


def set_language(language: FrontendLanguage) -> None:
    get_i18n().language = language


def t(key: str, **kwargs) -> str:
    return get_i18n().t(key, **kwargs)
