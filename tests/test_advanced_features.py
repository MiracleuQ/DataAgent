from types import SimpleNamespace

import pandas as pd
import pytest

from app.agents.reviewer import ReviewerAgent
from app.core.artifacts import Artifact
from app.core.context import DataContext
from app.core.eda import generate_eda_report


class ReviewLLM:
    def __init__(self):
        self.messages = []

    async def chat(self, messages, temperature=0.2, model=None, tools=None):
        self.messages.append(messages)
        return SimpleNamespace(content="Review: claims are supported; mention missing values.", tool_calls=None)


def test_context_stores_artifacts_with_stable_ids():
    context = DataContext()
    artifact = Artifact(kind="table", title="Profile", summary="Dataset profile", data={"rows": 3})

    stored = context.add_artifact(artifact)

    assert stored.id.startswith("artifact_")
    assert context.artifacts[0].id == stored.id
    assert context.artifact_summary() == "table: Profile - Dataset profile"


def test_add_dataframe_can_generate_auto_eda_artifact():
    context = DataContext()
    context.add_dataframe(
        "sales",
        pd.DataFrame({"region": ["east", "west", "east", "east", "east"], "amount": [10, 11, 12, 13, 1000]}),
        auto_profile=True,
    )

    assert len(context.artifacts) == 1
    artifact = context.artifacts[0]
    assert artifact.kind == "eda"
    assert artifact.title == "EDA: sales"
    assert artifact.data["dataset"] == "sales"
    assert artifact.data["shape"] == {"rows": 5, "columns": 2}
    assert any(finding["type"] == "potential_outliers" for finding in artifact.data["findings"])


def test_generate_eda_report_detects_missing_values_and_correlations():
    df = pd.DataFrame(
        {
            "a": [1.0, 2.0, None, 4.0],
            "b": [2.0, 4.0, 6.0, 8.0],
            "category": ["x", "x", "x", "y"],
        }
    )

    report = generate_eda_report("sample", df)

    assert report["dataset"] == "sample"
    assert any(finding["type"] == "missing_values" and finding["column"] == "a" for finding in report["findings"])
    assert any(finding["type"] == "high_cardinality_skew" and finding["column"] == "category" for finding in report["findings"])
    assert "correlations" in report


@pytest.mark.asyncio
async def test_reviewer_agent_reviews_report_against_context_and_artifacts():
    context = DataContext()
    context.add_dataframe("sales", pd.DataFrame({"amount": [1, 2, 3]}), auto_profile=True)
    context.add_result("final_report", "Sales increased to 3.")
    llm = ReviewLLM()
    reviewer = ReviewerAgent(llm_client=llm)

    result = await reviewer.run("review the final report", context)

    assert result.success is True
    assert result.output.startswith("Review:")
    assert context.get_result("review_report") == result.output
    assert "Artifacts:" in llm.messages[0][-1]["content"]
