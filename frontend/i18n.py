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
        "review": "审阅",
        "artifacts": "产出物",
        "agent_details": "🔍 Agent 执行详情",
        "analysis_failed": "分析失败：\n{errors}",
        "analysis_completed": "分析完成。",
        "error_occurred": "执行出错：{error}",
        "export": "导出",
        "export_excel": "导出 Excel",
        "export_csv": "导出 CSV",
        "export_json": "导出 JSON",
        "export_markdown": "导出 Markdown",
        "language": "语言",
        "chinese": "中文",
        "english": "English",
        # Welcome section
        "welcome_title": "欢迎使用 DataAgent ✦",
        "welcome_desc": "你的智能数据分析助手。上传数据，用自然语言提问，DataAgent 自动分析、可视化并生成报告。",
        "feature_analysis": "智能分析",
        "feature_analysis_desc": "自动检测数据模式，深度分析",
        "feature_viz": "AI 可视化",
        "feature_viz_desc": "AI 驱动生成精美图表",
        "feature_report": "自动报告",
        "feature_report_desc": "生成专业分析报告",
        "feature_anomaly": "异常检测",
        "feature_anomaly_desc": "自动识别异常数据",
        "try_asking": "试试这样问：",
        "ask_trend": "📊 分析销售趋势",
        "ask_top": "📈 查看 Top 产品",
        "ask_anomaly": "🔍 发现异常数据",
        "ask_report": "📋 生成分析报告",
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
        # Welcome section
        "welcome_title": "Welcome to DataAgent ✦",
        "welcome_desc": "Your intelligent data analysis assistant. Upload data, ask questions in natural language, and DataAgent will automatically analyze, visualize, and generate reports.",
        "feature_analysis": "Smart Analysis",
        "feature_analysis_desc": "Automatically detect data patterns and analyze",
        "feature_viz": "AI Visualization",
        "feature_viz_desc": "Generate beautiful charts with AI",
        "feature_report": "Auto Reports",
        "feature_report_desc": "Generate professional analysis reports",
        "feature_anomaly": "Anomaly Detection",
        "feature_anomaly_desc": "Identify outliers automatically",
        "try_asking": "Try asking:",
        "ask_trend": "📊 Analyze sales trends",
        "ask_top": "📈 Show top products",
        "ask_anomaly": "🔍 Find anomalies",
        "ask_report": "📋 Generate report",
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
