from typing import Any, Dict
import pandas as pd
import numpy as np


def describe_data(df: pd.DataFrame) -> Dict[str, Any]:
    return {"shape": list(df.shape), "columns": list(df.columns), "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}, "describe": df.describe(include="all").to_dict(), "missing": df.isnull().sum().to_dict()}


def group_aggregate(df: pd.DataFrame, group_by: str, agg_col: str, agg_func: str = "sum", top_n: int = 10) -> pd.DataFrame:
    result = df.groupby(group_by)[agg_col].agg(agg_func).sort_values(ascending=False).head(top_n)
    return result.reset_index()


def correlation(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    numeric = df.select_dtypes(include=["number"])
    if columns:
        numeric = numeric[[c for c in columns if c in numeric.columns]]
    return numeric.corr()


def detect_anomaly(df: pd.DataFrame, column: str, method: str = "iqr") -> pd.DataFrame:
    if method == "iqr":
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        mask = (df[column] < Q1 - 1.5 * IQR) | (df[column] > Q3 + 1.5 * IQR)
        return df[mask]
    elif method == "zscore":
        from scipy import stats
        clean = df[column].dropna()
        z = np.abs(stats.zscore(clean))
        anomaly_mask = z > 3
        return df.loc[clean.index[anomaly_mask]]
    return pd.DataFrame()


def get_analysis_tools():
    from app.tools.registry import Tool
    return [
        Tool(name="describe_data", description="Get statistical description", parameters={"type": "object", "properties": {}}, function=describe_data),
        Tool(name="group_aggregate", description="Group by and aggregate", parameters={"type": "object", "properties": {"group_by": {"type": "string"}, "agg_col": {"type": "string"}, "agg_func": {"type": "string", "enum": ["sum", "mean", "count", "min", "max"], "default": "sum"}, "top_n": {"type": "integer", "default": 10}}, "required": ["group_by", "agg_col"]}, function=group_aggregate),
        Tool(name="correlation", description="Calculate correlation matrix", parameters={"type": "object", "properties": {"columns": {"type": "array", "items": {"type": "string"}}}}, function=correlation),
        Tool(name="detect_anomaly", description="Detect anomalies", parameters={"type": "object", "properties": {"column": {"type": "string"}, "method": {"type": "string", "enum": ["iqr", "zscore"], "default": "iqr"}}, "required": ["column"]}, function=detect_anomaly),
    ]
