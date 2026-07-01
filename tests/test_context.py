import pandas as pd
from app.core.artifacts import Artifact
from app.core.context import DataContext


def test_add_and_get_dataframe():
    ctx = DataContext()
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    ctx.add_dataframe("test", df)
    result = ctx.get_dataframe("test")
    assert result is not None
    assert len(result) == 3


def test_list_dataframes():
    ctx = DataContext()
    ctx.add_dataframe("a", pd.DataFrame({"x": [1]}))
    ctx.add_dataframe("b", pd.DataFrame({"y": [2]}))
    assert ctx.list_dataframes() == ["a", "b"]


def test_add_analysis_result():
    ctx = DataContext()
    ctx.add_result("top10", {"data": [1, 2, 3]})
    assert ctx.get_result("top10") == {"data": [1, 2, 3]}


def test_add_chart():
    ctx = DataContext()
    ctx.add_chart("/tmp/chart.png")
    assert len(ctx.charts) == 1


def test_summary_cache_is_invalidated_by_context_outputs():
    ctx = DataContext()

    assert ctx.summary() == "Empty context"

    ctx.add_result("answer", {"value": 42})
    assert "Analysis result: answer" in ctx.summary()

    ctx.add_chart("/tmp/chart.png")
    assert "Charts: 1 generated" in ctx.summary()

    ctx.add_artifact(Artifact(kind="note", title="Finding", summary="Important"))
    assert "Artifacts: 1 available" in ctx.summary()
