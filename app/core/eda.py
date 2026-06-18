from typing import Any, Dict, List

import pandas as pd
from pandas.api.types import is_numeric_dtype
from app.utils.serialization import json_safe_value


def _missing_findings(df: pd.DataFrame) -> List[Dict[str, Any]]:
    findings = []
    row_count = len(df)
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if missing_count:
            findings.append(
                {
                    "type": "missing_values",
                    "column": str(col),
                    "count": missing_count,
                    "pct": round((missing_count / row_count * 100) if row_count else 0, 2),
                }
            )
    return findings


def _outlier_findings(df: pd.DataFrame) -> List[Dict[str, Any]]:
    findings = []
    for col in df.columns:
        series = df[col].dropna()
        if series.empty or not is_numeric_dtype(series):
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = series[(series < lower) | (series > upper)]
        if not outliers.empty:
            findings.append(
                {
                    "type": "potential_outliers",
                    "column": str(col),
                    "count": int(len(outliers)),
                    "lower_bound": json_safe_value(lower),
                    "upper_bound": json_safe_value(upper),
                    "examples": [json_safe_value(v) for v in outliers.head(5).tolist()],
                }
            )
    return findings


def _category_findings(df: pd.DataFrame) -> List[Dict[str, Any]]:
    findings = []
    row_count = len(df)
    for col in df.select_dtypes(exclude=["number"]).columns:
        non_null = df[col].dropna().astype(str)
        if non_null.empty:
            continue
        top_value = non_null.value_counts().iloc[0]
        top_share = top_value / row_count if row_count else 0
        if top_share >= 0.7:
            findings.append(
                {
                    "type": "high_cardinality_skew",
                    "column": str(col),
                    "top_share_pct": round(top_share * 100, 2),
                }
            )
    return findings


def _correlations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    numeric = df.select_dtypes(include=["number"])
    if numeric.shape[1] < 2:
        return []
    corr = numeric.corr(numeric_only=True)
    pairs = []
    for i, col_a in enumerate(corr.columns):
        for col_b in corr.columns[i + 1 :]:
            value = corr.loc[col_a, col_b]
            if pd.notna(value) and abs(value) >= 0.7:
                pairs.append({"columns": [str(col_a), str(col_b)], "correlation": round(float(value), 4)})
    return pairs


def generate_eda_report(name: str, df: pd.DataFrame) -> Dict[str, Any]:
    findings = []
    findings.extend(_missing_findings(df))
    findings.extend(_outlier_findings(df))
    findings.extend(_category_findings(df))
    correlations = _correlations(df)
    if correlations:
        findings.append({"type": "strong_correlations", "pairs": correlations})

    return {
        "dataset": name,
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "columns": [str(col) for col in df.columns],
        "findings": findings,
        "correlations": correlations,
    }
