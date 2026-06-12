from app.tools.registry import Tool, ToolRegistry


def test_register_and_get():
    registry = ToolRegistry()
    tool = Tool(name="read_csv", description="Read a CSV file", parameters={"type": "object", "properties": {"path": {"type": "string"}}}, function=lambda path: f"read {path}")
    registry.register(tool)
    assert registry.get("read_csv") is not None
    assert registry.get("nonexistent") is None


def test_list_tools():
    registry = ToolRegistry()
    registry.register(Tool(name="a", description="a", parameters={}, function=lambda: None))
    registry.register(Tool(name="b", description="b", parameters={}, function=lambda: None))
    names = [t.name for t in registry.list_tools()]
    assert names == ["a", "b"]


def test_to_openai_tools():
    registry = ToolRegistry()
    registry.register(Tool(name="read_csv", description="Read a CSV file", parameters={"type": "object", "properties": {"path": {"type": "string"}}}, function=lambda path: path))
    openai_tools = registry.to_openai_tools()
    assert len(openai_tools) == 1
    assert openai_tools[0]["type"] == "function"
    assert openai_tools[0]["function"]["name"] == "read_csv"


def test_call_tool():
    registry = ToolRegistry()
    registry.register(Tool(name="add", description="Add two numbers", parameters={"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}}, function=lambda a, b: a + b))
    result = registry.call("add", a=3, b=4)
    assert result == 7
