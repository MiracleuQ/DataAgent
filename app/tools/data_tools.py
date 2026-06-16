import io
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


def _is_within_path(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_allowed_path(path: str, allowed_root: str = "data") -> Path:
    root = Path(allowed_root).resolve()
    raw_path = Path(path)
    candidate = raw_path.resolve() if raw_path.is_absolute() else (Path.cwd() / raw_path).resolve()
    if not _is_within_path(candidate, root) and not raw_path.is_absolute():
        candidate = (root / raw_path).resolve()
    if not _is_within_path(candidate, root):
        raise PermissionError(f"File access is restricted to '{root}'")
    return candidate


def _validate_read_query(query: str) -> None:
    normalized = query.strip().lower()
    if not normalized.startswith(("select", "with")):
        raise PermissionError("Only read-only SELECT queries are allowed")
    if ";" in normalized.rstrip(";"):
        raise PermissionError("Multiple SQL statements are not allowed")


def _host_is_private(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return False
        addresses = []
        for info in infos:
            try:
                addresses.append(ipaddress.ip_address(info[4][0]))
            except ValueError:
                continue

    return any(
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
        for address in addresses
    )


def _validate_api_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise PermissionError("Only HTTP and HTTPS URLs are allowed")
    if not parsed.hostname:
        raise PermissionError("API URL must include a host")
    if _host_is_private(parsed.hostname):
        raise PermissionError("Local and private network API targets are not allowed")


def read_file(path: str, allowed_root: str = "data") -> pd.DataFrame:
    p = _resolve_allowed_path(path, allowed_root=allowed_root)
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

    _validate_read_query(query)
    engine = create_engine(connection_string)
    return pd.read_sql(query, engine)


def call_api(url: str, method: str = "GET", headers: dict = None, body: dict = None) -> pd.DataFrame:
    import httpx

    _validate_api_url(url)
    with httpx.Client(timeout=30) as client:
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
