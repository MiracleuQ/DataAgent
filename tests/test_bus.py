import pytest
from app.core.bus import Message, MessageBus


@pytest.mark.asyncio
async def test_send_and_receive():
    bus = MessageBus()
    msg = Message(sender="coordinator", receiver="analyst", content="analyze data", msg_type="task")
    await bus.send(msg)
    messages = await bus.receive("analyst")
    assert len(messages) == 1
    assert messages[0].content == "analyze data"


@pytest.mark.asyncio
async def test_receive_clears_inbox():
    bus = MessageBus()
    await bus.send(Message(sender="a", receiver="b", content="hello", msg_type="info"))
    await bus.receive("b")
    messages = await bus.receive("b")
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_broadcast():
    bus = MessageBus()
    await bus.broadcast(sender="coordinator", content="task complete", msg_type="info")
    assert len(await bus.receive("analyst")) == 1
    assert len(await bus.receive("visualizer")) == 1
