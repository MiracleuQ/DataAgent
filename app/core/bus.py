import hashlib
import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class Message:
    sender: str
    receiver: str
    content: str
    msg_type: Literal["task", "result", "error", "info", "data_request", "data_response"] = "info"
    metadata: Dict = field(default_factory=dict)


class MessageBus:
    def __init__(self):
        self._inboxes: Dict[str, List[Message]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._history: List[Message] = []
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._subscriptions: Dict[str, List[str]] = defaultdict(list)

    async def send(self, message: Message) -> None:
        async with self._lock:
            self._inboxes[message.receiver].append(message)
            self._history.append(message)
            logger.debug("Message sent: %s -> %s [%s]", message.sender, message.receiver, message.msg_type)

        handlers = self._handlers.get(message.receiver, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error("Handler error for %s: %s", message.receiver, e)

    async def receive(self, agent_id: str) -> List[Message]:
        async with self._lock:
            messages = self._inboxes.pop(agent_id, [])
            logger.debug("Messages received by %s: %d", agent_id, len(messages))
            return messages

    async def receive_with_timeout(self, agent_id: str, timeout: float = 1.0) -> List[Message]:
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            async with self._lock:
                if self._inboxes[agent_id]:
                    messages = self._inboxes.pop(agent_id, [])
                    logger.debug("Messages received by %s: %d", agent_id, len(messages))
                    return messages
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                return []
            await asyncio.sleep(min(0.05, remaining))

    async def broadcast(self, sender: str, content: str, msg_type: Literal["task", "result", "error", "info", "data_request", "data_response"] = "info") -> None:
        known_agents = {"coordinator", "data_engineer", "analyst", "visualizer", "reporter", "reviewer"}
        for agent in known_agents:
            if agent != sender:
                await self.send(Message(sender=sender, receiver=agent, content=content, msg_type=msg_type))

    async def request_data(self, sender: str, receiver: str, query: str, metadata: Dict[str, Any] = None) -> Optional[Message]:
        request_id = hashlib.md5(f"{sender}:{receiver}:{query}".encode()).hexdigest()[:16]
        await self.send(Message(
            sender=sender,
            receiver=receiver,
            content=query,
            msg_type="data_request",
            metadata={"request_id": request_id, **(metadata or {})},
        ))
        messages = await self.receive_with_timeout(sender, timeout=5.0)
        for msg in messages:
            if msg.msg_type == "data_response" and msg.metadata.get("request_id") == request_id:
                return msg
        return None

    def subscribe(self, agent_id: str, msg_type: str, handler: Callable) -> None:
        self._handlers[agent_id].append(handler)
        self._subscriptions[agent_id].append(msg_type)
        logger.debug("Agent %s subscribed to %s messages", agent_id, msg_type)

    async def get_history(self, agent_id: Optional[str] = None, msg_type: Optional[str] = None) -> List[Message]:
        async with self._lock:
            history = list(self._history)
            if agent_id:
                history = [m for m in history if m.sender == agent_id or m.receiver == agent_id]
            if msg_type:
                history = [m for m in history if m.msg_type == msg_type]
            return history
