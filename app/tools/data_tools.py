import io
from pathlib import Path
import pandas as pd


def read_file(path: str) -> pd.DataFrame:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(p)
    elif suffix in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    elif suffix == ".json":
        return pd.read_json(p)
    elif suffix == ".parquet":
        return pd.read_parquet(p)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def read_sql(connection_string: str, query: str) -> pd.DataFrame:
    from sqlalchemy import create_engine
    engine = create_engine(connection_string)
    return pd.read_sql(query, engine)


def call_api(url: str, method: str = "GET", headers: dict = None, body: dict = None) -> pd.DataFrame:
    import httpx
    client = httpx.Client(timeout=30)
    if method.upper() == "GET":
        resp = client.get(url, headers=headers)
    else:
        resp = client.post(url, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict):
        return pd.DataFrame([data])
    raise ValueError("Unexpected API response format")


def parse_text(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text), sep=None, engine="python")


def clean_data(df: pd.DataFrame, drop_duplicates: bool = True, fill_na: str = "median") -> pd.DataFrame:
    result = df.copy()
    if drop_duplicates:
        result = result.drop_duplicates()
    for col in result.columns:
        if result[col].isna().any():
            if fill_na == "median" and result[col].dtype in ["int64", "float64"]:
                result[col] = result[col].fillna(result[col].median())
            elif fill_na == "mode":
                result[col] = result[col].fillna(result[col].mode().iloc[0] if not result[col].mode().empty else "unknown")
            else:
                result[col] = result[col].fillna(0)
    return result


def get_data_tools():
    from app.tools.registry import Tool
    return [
        Tool(name="read_file", description="Read a data file (CSV, Excel, JSON, Parquet)", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, function=read_file),
        Tool(name="read_sql", description="Execute SQL query", parameters={"type": "object", "properties": {"connection_string": {"type": "string"}, "query": {"type": "string"}}, "required": ["connection_string", "query"]}, function=read_sql),
        Tool(name="call_api", description="Call REST API", parameters={"type": "object", "properties": {"url": {"type": "string"}, "method": {"type": "string", "default": "GET"}}, "required": ["url"]}, function=call_api),
        Tool(name="parse_text", description="Parse pasted text data", parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, function=parse_text),
        Tool(name="clean_data", description="Clean DataFrame", parameters={"type": "object", "properties": {"drop_duplicates": {"type": "boolean", "default": True}, "fill_na": {"type": "string", "enum": ["median", "mode", "zero"], "default": "median"}}}, function=clean_data),
    ]
