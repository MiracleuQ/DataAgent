from typing import Any, Dict, List, Optional
import pandas as pd
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataContext:
    def __init__(self):
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.charts: List[str] = []
        self.metadata: Dict[str, Any] = {}
        logger.info("DataContext initialized")

    def add_dataframe(self, name: str, df: pd.DataFrame) -> None:
        self.dataframes[name] = df
        logger.info(f"DataFrame '{name}' added: {len(df)} rows, {len(df.columns)} columns")

    def get_dataframe(self, name: str) -> Optional[pd.DataFrame]:
        df = self.dataframes.get(name)
        if df is None:
            logger.warning(f"DataFrame '{name}' not found")
        return df

    def list_dataframes(self) -> List[str]:
        return list(self.dataframes.keys())

    def add_result(self, key: str, value: Any) -> None:
        self.analysis_results[key] = value
        logger.info(f"Analysis result added: {key}")

    def get_result(self, key: str) -> Any:
        result = self.analysis_results.get(key)
        if result is None:
            logger.warning(f"Analysis result '{key}' not found")
        return result

    def add_chart(self, path: str) -> None:
        self.charts.append(path)
        logger.info(f"Chart added: {path}")

    def summary(self) -> str:
        parts = []
        for name, df in self.dataframes.items():
            parts.append(f"DataFrame '{name}': {len(df)} rows, {len(df.columns)} columns")
        for key in self.analysis_results:
            parts.append(f"Analysis result: {key}")
        if self.charts:
            parts.append(f"Charts: {len(self.charts)} generated")
        return "\n".join(parts) if parts else "Empty context"
