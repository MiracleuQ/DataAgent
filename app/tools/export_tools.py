import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def export_to_excel(
    dataframes: Dict[str, pd.DataFrame],
    output_path: str,
    sheet_name: Optional[str] = None,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in dataframes.items():
            sheet = sheet_name or name[:31]
            df.to_excel(writer, sheet_name=sheet, index=False)
            logger.info("Exported DataFrame '%s' to sheet '%s'", name, sheet)

    logger.info("Excel export completed: %s", path)
    return str(path)


def export_to_csv(
    df: pd.DataFrame,
    output_path: str,
    encoding: str = "utf-8-sig",
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding=encoding)
    logger.info("CSV export completed: %s", path)
    return str(path)


def export_to_json(
    data: Any,
    output_path: str,
    indent: int = 2,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, default=str)

    logger.info("JSON export completed: %s", path)
    return str(path)


def export_to_markdown(
    report: str,
    charts: List[str],
    output_path: str,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = report + "\n\n"
    if charts:
        content += "## Charts\n\n"
        for chart in charts:
            chart_name = Path(chart).stem
            content += f"![{chart_name}]({chart})\n\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Markdown export completed: %s", path)
    return str(path)


def export_to_parquet(
    df: pd.DataFrame,
    output_path: str,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info("Parquet export completed: %s", path)
    return str(path)


EXPORT_FORMATS = {
    "excel": export_to_excel,
    "csv": export_to_csv,
    "json": export_to_json,
    "markdown": export_to_markdown,
    "parquet": export_to_parquet,
}


def export_data(
    format_type: str,
    output_path: str,
    dataframes: Optional[Dict[str, pd.DataFrame]] = None,
    report: Optional[str] = None,
    charts: Optional[List[str]] = None,
    data: Any = None,
) -> str:
    if format_type not in EXPORT_FORMATS:
        raise ValueError(f"Unsupported format: {format_type}. Available: {list(EXPORT_FORMATS.keys())}")

    if format_type == "excel":
        if not dataframes:
            raise ValueError("Excel export requires dataframes")
        return export_to_excel(dataframes, output_path)
    elif format_type == "csv":
        if not dataframes or len(dataframes) != 1:
            raise ValueError("CSV export requires exactly one dataframe")
        df = list(dataframes.values())[0]
        return export_to_csv(df, output_path)
    elif format_type == "json":
        if data is None:
            raise ValueError("JSON export requires data")
        return export_to_json(data, output_path)
    elif format_type == "markdown":
        return export_to_markdown(report or "", charts or [], output_path)
    elif format_type == "parquet":
        if not dataframes or len(dataframes) != 1:
            raise ValueError("Parquet export requires exactly one dataframe")
        df = list(dataframes.values())[0]
        return export_to_parquet(df, output_path)
    else:
        raise ValueError(f"Unsupported format: {format_type}")
