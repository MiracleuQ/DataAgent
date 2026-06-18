import threading
from typing import Any, Dict, List, Optional
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype
from app.core.artifacts import Artifact
from app.core.eda import generate_eda_report
from app.utils.logger import setup_logger
from app.utils.serialization import json_safe_value

logger = setup_logger(__name__)


class DataContext:
    """
    Shared data context for agent collaboration.

    Threading model:
    - Uses ``threading.Lock`` to serialize mutations to shared state
      (dataframes, analysis_results, charts, artifacts).
    - All lock-held operations are O(1) dict/list mutations (microseconds),
      so the lock never blocks the asyncio event loop for a meaningful duration.
    - ``add_dataframe(auto_profile=True)`` generates EDA reports OUTSIDE the
      lock and then calls ``add_artifact`` (which acquires the lock only for a
      brief list append). This keeps the lock scope minimal.
    - In CPython, dict assignments and list appends are GIL-atomic, so
      ``threading.Lock`` is safe even when called from async code.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.charts: List[str] = []
        self.artifacts: List[Artifact] = []
        self.metadata: Dict[str, Any] = {}
        self._profile_cache: Dict[str, Dict[str, Any]] = {}
        self._summary_cache: Optional[str] = None
        logger.info("DataContext initialized")

    def add_dataframe(self, name: str, df: pd.DataFrame, auto_profile: bool = False) -> None:
        with self._lock:
            self.dataframes[name] = df
            self._profile_cache.pop(name, None)
            self._summary_cache = None
        logger.info(f"DataFrame '{name}' added: {len(df)} rows, {len(df.columns)} columns")
        if auto_profile:
            report = generate_eda_report(name, df)
            self.add_artifact(
                Artifact(
                    kind="eda",
                    title=f"EDA: {name}",
                    summary=f"{len(report['findings'])} automated finding(s) for {name}",
                    data=report,
                    metadata={"dataset": name},
                )
            )

    def get_dataframe(self, name: str) -> Optional[pd.DataFrame]:
        with self._lock:
            df = self.dataframes.get(name)
        if df is None:
            logger.warning(f"DataFrame '{name}' not found")
        return df

    def list_dataframes(self) -> List[str]:
        with self._lock:
            return list(self.dataframes.keys())

    def add_result(self, key: str, value: Any) -> None:
        with self._lock:
            self.analysis_results[key] = value
        logger.info(f"Analysis result added: {key}")

    def get_result(self, key: str) -> Any:
        with self._lock:
            result = self.analysis_results.get(key)
        if result is None:
            logger.warning(f"Analysis result '{key}' not found")
        return result

    def add_chart(self, path: str) -> None:
        with self._lock:
            self.charts.append(path)
        logger.info(f"Chart added: {path}")

    def add_artifact(self, artifact: Artifact) -> Artifact:
        with self._lock:
            self.artifacts.append(artifact)
        logger.info(f"Artifact added: {artifact.kind} - {artifact.title}")
        return artifact

    def artifact_summary(self) -> str:
        if not self.artifacts:
            return "No artifacts"
        return "\n".join(f"{artifact.kind}: {artifact.title} - {artifact.summary}" for artifact in self.artifacts)

    def _json_safe_value(self, value: Any) -> Any:
        return json_safe_value(value)

    def data_profile(self, name: str, sample_size: int = 3, top_n: int = 5) -> Dict[str, Any]:
        df = self.get_dataframe(name)
        if df is None:
            raise KeyError(f"DataFrame '{name}' not found")

        fingerprint = (len(df), len(df.columns))
        cached = self._profile_cache.get(name)
        if cached and cached.get("_fingerprint") == fingerprint:
            return cached

        columns: Dict[str, Dict[str, Any]] = {}
        row_count = len(df)
        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            profile: Dict[str, Any] = {
                "dtype": str(series.dtype),
                "missing_count": missing_count,
                "missing_pct": round((missing_count / row_count * 100) if row_count else 0, 2),
                "unique_count": int(series.nunique(dropna=True)),
            }

            non_null = series.dropna()
            if not non_null.empty and is_numeric_dtype(series):
                profile["min"] = self._json_safe_value(non_null.min())
                profile["max"] = self._json_safe_value(non_null.max())
                profile["mean"] = self._json_safe_value(non_null.mean())
            elif not non_null.empty and is_datetime64_any_dtype(series):
                profile["min"] = self._json_safe_value(non_null.min())
                profile["max"] = self._json_safe_value(non_null.max())
            else:
                value_counts = non_null.astype(str).value_counts().head(top_n)
                profile["top_values"] = {str(k): int(v) for k, v in value_counts.items()}

            columns[str(col)] = profile

        sample_rows = [
            {str(key): self._json_safe_value(value) for key, value in row.items()}
            for row in df.head(sample_size).to_dict(orient="records")
        ]
        result = {
            "name": name,
            "shape": {"rows": row_count, "columns": len(df.columns)},
            "columns": columns,
            "sample_rows": sample_rows,
            "_fingerprint": fingerprint,
        }
        self._profile_cache[name] = result
        return result

    def summary(self) -> str:
        with self._lock:
            if self._summary_cache is not None:
                return self._summary_cache
            snapshot = (dict(self.dataframes), dict(self.analysis_results), list(self.charts), list(self.artifacts))
        dataframes, analysis_results, charts, artifacts = snapshot
        parts = []
        for name, df in dataframes.items():
            profile = self.data_profile(name)
            column_bits = []
            for col, info in profile["columns"].items():
                bit = f"{col}({info['dtype']}, missing {info['missing_pct']}%)"
                if "min" in info and "max" in info:
                    bit += f", range {info['min']}..{info['max']}"
                elif "top_values" in info:
                    bit += f", top {info['top_values']}"
                column_bits.append(bit)
            parts.append(
                f"DataFrame '{name}': {len(df)} rows, {len(df.columns)} columns; "
                f"columns: {', '.join(column_bits)}; sample: {profile['sample_rows']}"
            )
        for key in analysis_results:
            parts.append(f"Analysis result: {key}")
        if charts:
            parts.append(f"Charts: {len(charts)} generated")
        if artifacts:
            parts.append(f"Artifacts: {len(artifacts)} available")
        result = "\n".join(parts) if parts else "Empty context"
        with self._lock:
            self._summary_cache = result
        return result
