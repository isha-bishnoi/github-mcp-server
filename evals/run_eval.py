
import json
from pathlib import Path
import sys
import re
from collections import defaultdict

dataset_name = sys.argv[1] if len(sys.argv) > 1 else "queries.json"
QUERIES_FILE = Path(__file__).parent / dataset_name


def predict_tool(query):
    query = query.lower()

    # 1. Pull request-related queries
    if "pull request" in query or "pull requests" in query or re.search(r"\bpr\b", query):
        return "list_pull_requests"

    # 2. List repositories belonging to a GitHub user
    repository_list_keywords = [
        "repositories", "projects",
        "all repository", "all repo",
        "list repository", "list repo",
        "repository owned", "repositories owned",
        "repository belonging", "repositories belonging",
        "repository has", "repositories has",
        "repository under", "repositories under",
        "repository in", "repositories in",
        "every project",
    ]

    if any(keyword in query for keyword in repository_list_keywords):
        return "list_repositories"

    # 3. Individual repository metadata
    repository_metadata_keywords = [
        "repository", "star", "branch", "description",
    "github url", "github page",
    "basic information", "how popular",
    "open issues count", "number of open issues",
    "metadata", "get details",
    ]

    if (
        any(keyword in query for keyword in repository_metadata_keywords)
        or re.search(r"\brepo\b", query)
    ):
        return "get_repository"

    # 4. Issue-list queries
    if "issue" in query or "bug" in query:
        return "list_issues"

    return None



def main():
    with open(QUERIES_FILE, "r", encoding="utf-8") as file:
        queries = json.load(file)

    correct = 0
    failures = []

    tool_stats = {
    "get_repository": {"correct": 0, "total": 0},
    "list_repositories": {"correct": 0, "total": 0},
    "list_issues": {"correct": 0, "total": 0},
    "list_pull_requests": {"correct": 0, "total": 0}
    }

    confusion_matrix = defaultdict(lambda: defaultdict(int))

    for item in queries:
        predicted = predict_tool(item["query"])
        expected = item["expected_tool"]
        confusion_matrix[expected][predicted or "None"] += 1

        tool_stats[expected]["total"] += 1

        if predicted == expected:
          correct += 1
          tool_stats[expected]["correct"] += 1
        else:
            failures.append({
                "id": item["id"],
                "query": item["query"],
                "expected": expected,
                "predicted": predicted
            })

    total = len(queries)
    accuracy = (correct / total) * 100 if total else 0

    print(f"\nTotal queries: {total}")
    print(f"Correct predictions: {correct}")
    print(f"Incorrect predictions: {len(failures)}")
    print(f"Tool selection accuracy: {accuracy:.2f}%")

    
    # Per-tool accuracy
    print("\nPer-tool accuracy:")

    for tool, stats in tool_stats.items():
        tool_accuracy = (
            stats["correct"] / stats["total"] * 100
            if stats["total"] > 0 else 0
        )

        print(
            f"{tool}: {stats['correct']}/{stats['total']} "
            f"({tool_accuracy:.2f}%)"
        )

    # Confusion matrix
    print("\nConfusion Matrix:")

    tools = [
        "get_repository",
        "list_repositories",
        "list_issues",
        "list_pull_requests"
    ]

    header = f"{'Expected / Predicted':25}"

    for tool in tools:
        header += f"{tool[:15]:18}"

    print(header)

    for expected in tools:
        row = f"{expected:25}"

        for predicted in tools:
            row += f"{confusion_matrix[expected][predicted]:18}"

        print(row)


    
    if failures:
        print("\nFailed predictions:")
        for failure in failures:
            print(failure)


if __name__ == "__main__":
    main()
