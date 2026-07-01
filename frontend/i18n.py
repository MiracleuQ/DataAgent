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
        # Workbench redesign
        "brand_subtitle": "多 Agent 数据分析工作台",
        "status_ready": "已就绪",
        "status_waiting": "等待数据",
        "status_label": "状态",
        "rows_label": "行数",
        "latest_label": "最新数据",
        "no_dataset": "暂无数据集",
        "workspace_title": "分析工作台",
        "workspace_desc": "上传数据，选择分析模板，然后生成图表和管理层报告。",
        "metric_datasets": "数据集",
        "metric_rows_loaded": "已加载行数",
        "metric_rows_note": "当前上下文合计",
        "metric_outputs": "产出",
        "metric_outputs_note": "{charts} 个图表，{artifacts} 个产出物",
        "metric_findings": "发现",
        "metric_findings_note": "已保存的分析结果",
        "metric_upload_note": "上传 CSV、Excel、JSON 或 Parquet",
        "side_workspace": "工作区",
        "side_workspace_note": "上传数据后，可使用下方输入框或分析模板启动任务。",
        "side_data_source": "数据源",
        "side_active_datasets": "当前数据集",
        "side_no_data": "尚未加载数据。",
        "side_session": "会话",
        "templates_title": "分析模板",
        "templates_desc": "从一个聚焦的工作流开始，或在下方输入你的自定义需求。",
        "template_quality": "质量检查",
        "template_trend": "趋势分析",
        "template_anomaly": "异常扫描",
        "template_report": "管理报告",
        "prompt_quality": "请检查数据质量，识别缺失值、重复行、异常值和需要清洗的字段，并给出清洗建议。",
        "prompt_trend": "请按时间维度分析收入、利润和销量趋势，指出明显增长、下降和波动的原因。",
        "prompt_anomaly": "请识别销售额、利润、数量、折扣和评分中的异常记录，并说明这些异常对分析结论的影响。",
        "prompt_report": "请生成一份管理层经营分析报告，包含核心指标、趋势、地区、渠道、产品、异常风险和行动建议。",
        "tab_report": "报告",
        "tab_charts": "图表",
        "tab_review": "审阅",
        "tab_artifacts": "产出物",
        "tab_execution": "执行详情",
        "execution_tasks": "任务数",
        "execution_succeeded": "成功",
        "execution_failed": "失败",
        "no_charts": "本次运行没有生成图表。",
        "no_review_notes": "本次运行没有审阅意见。",
        "no_artifacts": "本次运行没有生成产出物。",
        "no_execution_details": "没有可用的执行详情。",
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
        # Workbench redesign
        "brand_subtitle": "Multi-agent analysis workbench",
        "status_ready": "Ready",
        "status_waiting": "Waiting for data",
        "status_label": "Status",
        "rows_label": "Rows",
        "latest_label": "Latest",
        "no_dataset": "No dataset",
        "workspace_title": "Analysis Workspace",
        "workspace_desc": "Load data, choose an analysis template, then ask for charts and a management-ready report.",
        "metric_datasets": "Datasets",
        "metric_rows_loaded": "Rows Loaded",
        "metric_rows_note": "Across active context",
        "metric_outputs": "Outputs",
        "metric_outputs_note": "{charts} charts, {artifacts} artifacts",
        "metric_findings": "Findings",
        "metric_findings_note": "Stored analysis results",
        "metric_upload_note": "Upload CSV, Excel, JSON, or Parquet",
        "side_workspace": "Workspace",
        "side_workspace_note": "Upload a dataset, then use the prompt box or a template to run analysis.",
        "side_data_source": "Data Source",
        "side_active_datasets": "Active Datasets",
        "side_no_data": "No data loaded yet.",
        "side_session": "Session",
        "templates_title": "Analysis Templates",
        "templates_desc": "Start from a focused workflow or type your own request below.",
        "template_quality": "Quality Check",
        "template_trend": "Trend Analysis",
        "template_anomaly": "Anomaly Scan",
        "template_report": "Executive Report",
        "prompt_quality": "Check data quality, identify missing values, duplicate rows, outliers, and fields that need cleaning. Provide cleaning recommendations.",
        "prompt_trend": "Analyze revenue, profit, and quantity trends over time. Highlight notable growth, declines, and volatility.",
        "prompt_anomaly": "Identify abnormal records in revenue, profit, quantity, discount, and rating. Explain how they affect the analysis.",
        "prompt_report": "Generate an executive business analysis report with KPIs, trends, region, channel, product, anomaly risks, and action recommendations.",
        "tab_report": "Report",
        "tab_charts": "Charts",
        "tab_review": "Review",
        "tab_artifacts": "Artifacts",
        "tab_execution": "Execution",
        "execution_tasks": "Tasks",
        "execution_succeeded": "Succeeded",
        "execution_failed": "Failed",
        "no_charts": "No charts generated for this run.",
        "no_review_notes": "No reviewer notes for this run.",
        "no_artifacts": "No artifacts generated for this run.",
        "no_execution_details": "No execution details available.",
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
