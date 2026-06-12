import pandas as pd
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
