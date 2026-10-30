import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.run_eval import predict_tool


@pytest.mark.parametrize(
    "query, expected",
    [
        ("Get details about octocat/Hello-World", "get_repository"),
        ("List all repositories owned by octocat", "list_repositories"),
        ("Show open issues in octocat/Hello-World", "list_issues"),
        ("Show pull requests in octocat/Hello-World", "list_pull_requests"),
        ("Tell me a joke", None),
    ],
)
def test_predict_tool(query, expected):
    assert predict_tool(query) == expected