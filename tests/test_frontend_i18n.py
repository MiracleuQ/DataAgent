from frontend.i18n import TRANSLATIONS, FrontendLanguage


WORKBENCH_KEYS = {
    "brand_subtitle",
    "status_ready",
    "status_waiting",
    "status_label",
    "rows_label",
    "latest_label",
    "no_dataset",
    "workspace_title",
    "workspace_desc",
    "metric_datasets",
    "metric_rows_loaded",
    "metric_rows_note",
    "metric_outputs",
    "metric_outputs_note",
    "metric_findings",
    "metric_findings_note",
    "metric_upload_note",
    "side_workspace",
    "side_workspace_note",
    "side_data_source",
    "side_active_datasets",
    "side_no_data",
    "side_session",
    "templates_title",
    "templates_desc",
    "template_quality",
    "template_trend",
    "template_anomaly",
    "template_report",
    "prompt_quality",
    "prompt_trend",
    "prompt_anomaly",
    "prompt_report",
    "tab_report",
    "tab_charts",
    "tab_review",
    "tab_artifacts",
    "tab_execution",
    "execution_tasks",
    "execution_succeeded",
    "execution_failed",
    "no_charts",
    "no_review_notes",
    "no_artifacts",
    "no_execution_details",
}


def test_workbench_i18n_keys_exist_for_all_languages():
    for language in FrontendLanguage:
        missing = WORKBENCH_KEYS - set(TRANSLATIONS[language])
        assert not missing, f"{language} missing translations: {sorted(missing)}"


def test_chinese_workbench_translations_are_not_english_placeholders():
    zh = TRANSLATIONS[FrontendLanguage.CHINESE]

    assert zh["side_workspace"] == "工作区"
    assert zh["templates_title"] == "分析模板"
    assert zh["template_quality"] == "质量检查"
    assert zh["tab_execution"] == "执行详情"
