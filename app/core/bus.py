import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Literal

logger = logging.getLogger(__name__)


@dataclass
class Message:
    sender: str
    receiver: str
    content: str
    msg_type: Literal["task", "result", "error", "info"] = "info"
    metadata: Dict = field(default_factory=dict)


class MessageBus:
    def __init__(self):
        self._inboxes: Dict[str, List[Message]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._history: List[Message] = []

    async def send(self, message: Message) -> None:
        async with self._lock:
            self._inboxes[message.receiver].append(message)
            self._history.append(message)
            logger.debug("Message sent: %s -> %s [%s]", message.sender, message.receiver, message.msg_type)

    async def receive(self, agent_id: str) -> List[Message]:
        async with self._lock:
            messages = self._inboxes.pop(agent_id, [])
            logger.debug("Messages received by %s: %d", agent_id, len(messages))
            return messages

    async def broadcast(self, sender: str, content: str, msg_type: Literal["task", "result", "error", "info"] = "info") -> None:
        agents = {"coordinator", "data_engineer", "analyst", "visualizer", "reporter"}
        for agent in agents:
            if agent != sender:
                await self.send(Message(sender=sender, receiver=agent, content=content, msg_type=msg_type))

    async def get_history(self) -> List[Message]:
        async with self._lock:
            return list(self._history)
