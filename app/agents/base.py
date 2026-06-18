import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from app.core.context import DataContext
from app.core.bus import MessageBus, Message
from app.tools.registry import ToolRegistry
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def resolve_dataframe(context: DataContext, args: Dict[str, Any], purpose: str = "operation") -> "pd.DataFrame":
    import pandas as pd
    df_name = args.pop("df_name", None) or (context.list_dataframes()[0] if context.list_dataframes() else None)
    if not df_name:
        raise ValueError(f"No dataframe is available for {purpose}")
    df = context.get_dataframe(df_name)
    if df is None:
        raise ValueError(f"DataFrame '{df_name}' not found")
    return df


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentResult:
    success: bool
    output: str
    agent_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0
    status: AgentStatus = AgentStatus.SUCCESS


class BaseAgent(ABC):
    def __init__(self, role: str, system_prompt: str, tools: Optional[ToolRegistry] = None, bus: Optional[MessageBus] = None, timeout: int = 120):
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self._bus = bus
        self._timeout = timeout
        self._history: List[Dict[str, str]] = []
        self._status = AgentStatus.IDLE
        self._last_run_time: Optional[float] = None
        logger.info(f"Agent '{role}' initialized (timeout={timeout}s)")

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def last_run_time(self) -> Optional[float]:
        return self._last_run_time

    def _build_messages(self, task: str) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self._history)
        messages.append({"role": "user", "content": task})
        return messages

    def _remember(self, task: str, result: str) -> None:
        self._history.append({"role": "user", "content": task})
        self._history.append({"role": "assistant", "content": result})
        if len(self._history) > 20:
            self._history = self._history[-20:]
            logger.info(f"Agent '{self.role}' history trimmed to last 20 messages")

    def _make_execute_tool(self, context: DataContext, purpose: str = "operation") -> Callable[[str, Dict[str, Any]], Any]:
        def execute_tool(func_name: str, args: Dict[str, Any]) -> Any:
            df_name = args.get("df_name") or (context.list_dataframes()[0] if context.list_dataframes() else None)
            df = resolve_dataframe(context, args, purpose)
            result = self.tools.call(func_name, df=df, **args)
            stored = result if not hasattr(result, "to_dict") else result.to_dict()
            if df_name:
                context.add_result(f"{func_name}_{df_name}", stored)
            return stored
        return execute_tool

    async def send_message(self, receiver: str, content: str, msg_type: str = "info", metadata: Dict[str, Any] = None) -> None:
        if self._bus:
            await self._bus.send(Message(
                sender=self.role,
                receiver=receiver,
                content=content,
                msg_type=msg_type,
                metadata=metadata or {},
            ))

    async def receive_messages(self) -> List[Message]:
        if self._bus:
            return await self._bus.receive(self.role)
        return []

    async def broadcast(self, content: str, msg_type: str = "info") -> None:
        if self._bus:
            await self._bus.broadcast(self.role, content, msg_type)

    async def run_with_timeout(self, task: str, context: DataContext) -> AgentResult:
        self._status = AgentStatus.RUNNING
        start_time = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                self.run(task, context),
                timeout=self._timeout,
            )
            result.duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._status = result.status
            self._last_run_time = result.duration_ms
            return result
        except asyncio.TimeoutError:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._status = AgentStatus.TIMEOUT
            self._last_run_time = duration_ms
            logger.warning(f"Agent '{self.role}' timed out after {duration_ms}ms")
            return AgentResult(
                success=False,
                output="",
                agent_id=self.role,
                error=f"Agent timed out after {self._timeout} seconds",
                duration_ms=duration_ms,
                status=AgentStatus.TIMEOUT,
            )
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._status = AgentStatus.FAILED
            self._last_run_time = duration_ms
            logger.error("Agent '%s' failed: %s", self.role, e, exc_info=True)
            return AgentResult(
                success=False,
                output="",
                agent_id=self.role,
                error=str(e),
                duration_ms=duration_ms,
                status=AgentStatus.FAILED,
            )

    @abstractmethod
    async def run(self, task: str, context: DataContext) -> AgentResult:
        raise NotImplementedError
