from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.core.context import DataContext
from app.tools.registry import ToolRegistry
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class AgentResult:
    success: bool
    output: str
    agent_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseAgent(ABC):
    def __init__(self, role: str, system_prompt: str, tools: Optional[ToolRegistry] = None):
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self._history: List[Dict[str, str]] = []
        logger.info(f"Agent '{role}' initialized")

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

    @abstractmethod
    async def run(self, task: str, context: DataContext) -> AgentResult:
        raise NotImplementedError
