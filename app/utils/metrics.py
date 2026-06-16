import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Metric:
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[float] = None


class MetricsCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._labels: Dict[str, Dict[str, str]] = {}
        self._start_time = time.time()

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] = self._counters.get(key, 0) + value
            self._labels[key] = labels or {}

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            self._labels[key] = labels or {}

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            self._labels[key] = labels or {}

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)

    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0)

    def get_histogram(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    def export_prometheus(self) -> str:
        lines = []
        lines.append("# HELP dataagent_uptime_seconds Total uptime in seconds")
        lines.append("# TYPE dataagent_uptime_seconds gauge")
        lines.append(f"dataagent_uptime_seconds {time.time() - self._start_time}")

        for key, value in self._counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")

        for key, value in self._gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")

        for key, values in self._histograms.items():
            base_name = key.split('{')[0]
            lines.append(f"# TYPE {base_name} histogram")
            if values:
                lines.append(f"{key}_count {len(values)}")
                lines.append(f"{key}_sum {sum(values)}")

        return "\n".join(lines)

    def export_json(self) -> Dict[str, Any]:
        return {
            "uptime_seconds": time.time() - self._start_time,
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: self.get_histogram(k.split('{')[0], self._labels.get(k))
                for k in self._histograms
            },
        }


_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def record_agent_execution(agent_name: str, duration_ms: float, success: bool) -> None:
    metrics = get_metrics()
    metrics.increment_counter("dataagent_agent_executions_total", labels={"agent": agent_name, "status": "success" if success else "failed"})
    metrics.observe_histogram("dataagent_agent_duration_ms", duration_ms, labels={"agent": agent_name})
    metrics.set_gauge("dataagent_agent_last_duration_ms", duration_ms, labels={"agent": agent_name})


def record_llm_call(model: str, duration_ms: float, success: bool) -> None:
    metrics = get_metrics()
    metrics.increment_counter("dataagent_llm_calls_total", labels={"model": model, "status": "success" if success else "failed"})
    metrics.observe_histogram("dataagent_llm_duration_ms", duration_ms, labels={"model": model})


def record_tool_call(tool_name: str, duration_ms: float) -> None:
    metrics = get_metrics()
    metrics.increment_counter("dataagent_tool_calls_total", labels={"tool": tool_name})
    metrics.observe_histogram("dataagent_tool_duration_ms", duration_ms, labels={"tool": tool_name})
