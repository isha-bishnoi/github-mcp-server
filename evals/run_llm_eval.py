
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# Load environment variables from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is not configured.")

client = Groq(api_key=api_key)

MODEL = "qwen/qwen3.8-27b"

# Load evaluation queries
QUERIES_FILE = Path(__file__).parent / "queries.json"

with open(QUERIES_FILE, "r") as file:
    queries = json.load(file)

# Optionally evaluate a single query by ID
if len(sys.argv) > 1:
    target_id = int(sys.argv[1])
    queries = [
        item for item in queries
        if item["id"] == target_id
    ]

    if not queries:
        raise ValueError(f"Query ID {target_id} not found.")


# Define the four MCP tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_repository",
            "description":(
    "Retrieve information about a public GitHub repository. "
    "Use this tool whenever the user asks about a repository, "
    "including requesting its GitHub page or URL."
),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"}
                },
                "required": ["owner", "repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_repositories",
            "description": "List public repositories belonging to a GitHub user or organization.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"}
                },
                "required": ["owner"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_issues",
            "description": (
    "List issues in a GitHub repository. "
    "Use state='open' when the user does not specify a state. "
    "Use state='closed' for closed issues. "
    "Use state='all' only when the user explicitly requests "
    "both open and closed issues or all issues."
),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "default": "open"
                    }
                },
                "required": ["owner", "repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_pull_requests",
            "description": (
    "List pull requests in a GitHub repository. "
    "Use state='open' when the user does not specify a state. "
    "Use state='closed' for closed pull requests. "
    "Use state='all' when the user explicitly requests "
    "both open and closed pull requests or all pull requests."
),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "default": "open"
                    }
                },
                "required": ["owner", "repo"]
            }
        }
    }
]


def normalize_arguments(tool_name, arguments):
    """
    Apply tool defaults before comparing extracted arguments
    with expected arguments.
    """
    normalized = dict(arguments)

    if tool_name in {"list_issues", "list_pull_requests"}:
        normalized.setdefault("state", "open")

    return normalized


results = []

for index, item in enumerate(queries, start=1):
    query_id = item["id"]
    query = item["query"]
    expected_tool = item["expected_tool"]
    expected_arguments = item["expected_arguments"]

    print(f"\nEvaluating query {index}/{len(queries)}...")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": query}
            ],
            tools=tools,
            tool_choice="auto",
            temperature=0
        )

        message = response.choices[0].message

        if message.tool_calls:
            selected_tool = message.tool_calls[0].function.name
            arguments = json.loads(
                message.tool_calls[0].function.arguments
            )
        else:
            selected_tool = None
            arguments = {}

        # Check tool selection
        tool_correct = selected_tool == expected_tool

        # Check arguments only when the selected tool is correct
        if tool_correct:
            actual_arguments = normalize_arguments(
                selected_tool, arguments
            )
            arguments_correct = actual_arguments == expected_arguments
        else:
            actual_arguments = arguments
            arguments_correct = False

        # Both tool and arguments must be correct
        overall_correct = tool_correct and arguments_correct

        results.append({
            "id": query_id,
            "query": query,
            "expected_tool": expected_tool,
            "selected_tool": selected_tool,
            "expected_arguments": expected_arguments,
            "arguments": arguments,
            "tool_correct": tool_correct,
            "arguments_correct": arguments_correct,
            "overall_correct": overall_correct,
            "error": None
        })

    except Exception as exc:
        print(f"API/Evaluation error: {exc}")
        results.append({
            "id": query_id,
            "query": query,
            "expected_tool": expected_tool,
            "selected_tool": None,
            "expected_arguments": expected_arguments,
            "arguments": {},
            "tool_correct": False,
            "arguments_correct": False,
            "overall_correct": False,
            "error": str(exc)
        })

         # Stop evaluation if the API rate limit is reached
        if getattr(exc, "status_code", None) == 429:
            print("\nRate limit reached. Stopping evaluation.")
            break

    result = results[-1]

    print(
        f"Expected tool: {result['expected_tool']} | "
        f"Selected tool: {result['selected_tool']} | "
        f"Tool correct: {result['tool_correct']}"
    )

    print(
        f"Expected arguments: {result['expected_arguments']} | "
        f"Actual arguments: {result['arguments']} | "
        f"Arguments correct: {result['arguments_correct']}"
    )


# Calculate evaluation metrics
successful_results = [
    result for result in results
    if result["error"] is None
]

total = len(queries)
successful_count = len(successful_results)
failed_count = total - successful_count

tool_correct_count = sum(
    result["tool_correct"] for result in successful_results
)

correct_tool_results = [
    result for result in successful_results
    if result["tool_correct"]
]

argument_correct_count = sum(
    result["arguments_correct"] for result in correct_tool_results
)

overall_correct_count = sum(
    result["overall_correct"] for result in successful_results
)

tool_accuracy = (
    tool_correct_count / successful_count * 100
    if successful_count else 0
)

argument_accuracy = (
    argument_correct_count / len(correct_tool_results) * 100
    if correct_tool_results else 0
)

overall_accuracy = (
    overall_correct_count / successful_count * 100
    if successful_count else 0
)


# Save detailed results
if len(sys.argv) > 1:
    output_file = Path(__file__).parent / "llm_eval_single_query_results.json"
else:
    output_file = Path(__file__).parent / "llm_eval_results.json"

with open(output_file, "w") as file:
    json.dump(results, file, indent=4)


# Print evaluation summary
print("\n========== EVALUATION SUMMARY ==========")
print(f"Model: {MODEL}")
print(f"Total queries: {total}")
print(f"Successfully evaluated: {successful_count}")
print(f"Failed/API errors: {failed_count}")

print("\nTool selection:")
print(f"Correct: {tool_correct_count}/{successful_count}")
print(f"Accuracy: {tool_accuracy:.2f}%")

print("\nArgument extraction:")
print(f"Correct: {argument_correct_count}/{len(correct_tool_results)}")
print(f"Accuracy: {argument_accuracy:.2f}%")

print("\nEnd-to-end:")
print(f"Correct tool + arguments: {overall_correct_count}/{successful_count}")
print(f"Accuracy: {overall_accuracy:.2f}%")

print(f"\nDetailed results saved to: {output_file}")
