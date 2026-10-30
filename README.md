# GitHub MCP Server

A read-only Model Context Protocol (MCP) server built in Python that enables AI applications to interact with GitHub repository data through structured tools.

The server uses the GitHub REST API to retrieve repository information, list repositories, view issues, and retrieve pull requests.

The project focuses on building a reliable MCP server with clear tool interfaces, error handling, retry mechanisms, and an evaluation framework for measuring tool-selection accuracy.

## Available Tools

The MCP server currently provides four read-only tools:

| Tool | Description |
|---|---|
| `get_repository` | Retrieves repository details such as description, default branch, stars, open issues count, and GitHub URL. |
| `list_repositories` | Lists public repositories owned by a specified GitHub user. |
| `list_issues` | Retrieves issues from a repository, with support for filtering by open, closed, or all issues. Pull requests are excluded. |
| `list_pull_requests` | Retrieves pull requests from a repository, with support for filtering by open, closed, or all pull requests. |

All tools use the GitHub REST API and perform read-only operations. They do not create, update, or delete GitHub resources.

## Architecture

The project follows a simple layered architecture:

```text
AI Application / MCP Client
          |
          | MCP Protocol
          v
     MCP Server
          |
          | Tool Selection & Execution
          v
    GitHub API Client
          |
          | HTTPS Requests
          v
     GitHub REST API
```

### How It Works

1. An MCP client connects to the server using the MCP protocol over standard input/output (stdio).
2. The client discovers the tools exposed by the server.
3. When a user requests GitHub information, the client invokes the appropriate tool.
4. The MCP server executes the tool and sends an HTTP request to the GitHub REST API.
5. The server processes the API response and returns structured information to the MCP client.

The server uses asynchronous HTTP requests through `httpx` and includes retry handling and error handling for API failures and network issues.

## Technology Stack

- **Python 3.13** – Primary programming language.
- **MCP SDK** – Implements the Model Context Protocol server.
- **httpx** – Handles asynchronous HTTP requests to the GitHub REST API.
- **python-dotenv** – Loads environment variables from the `.env` file.
- **pytest** – Provides automated unit and integration testing.
- **GitHub REST API** – Provides repository, issue, and pull request data.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd github-mcp-server
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Configure GitHub Authentication

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token
```

A GitHub personal access token is recommended to provide authenticated API access and higher API rate limits.

### 5. Run the MCP Server

```bash
python -m github_mcp.server
```

The server uses stdio transport and waits for connections from an MCP client.

## Testing

The project includes automated tests covering server functionality, API error handling, retry behavior, and tool-selection logic.

Run the complete test suite:

```bash
pytest -v
```

Run only the server tests:

```bash
pytest tests/test_server.py -v
```

Run only the evaluation tests:

```bash
pytest tests/test_evaluation.py -v
```

The current test suite contains **26 passing tests**.

## Evaluation Framework

The project includes a lightweight evaluation framework to measure how accurately natural-language queries are mapped to the appropriate MCP tools.

### Evaluation Approach

- Created a dataset of 50 natural-language queries with expected tool selections.
- Created a separate set of 20 additional queries to validate the classifier.
- Used a rule-based classifier to predict which MCP tool should handle each query.
- Compared predicted tools against expected tools.
- Generated accuracy metrics, per-tool accuracy, a confusion matrix, and failure details.

### Evaluation Metrics

The evaluation script reports:

- Overall tool-selection accuracy.
- Per-tool accuracy.
- Confusion matrix.
- Incorrect predictions and failure cases.

### Running the Evaluation

Run the original evaluation dataset:

```bash
python evals/run_eval.py
```

Run the additional query set:

```bash
python evals/run_eval.py unseen_queries.json
```

**Note:** The classifier uses keyword-based rules rather than an LLM. The additional query set was also used during classifier refinement, so its results should be treated as development/validation results rather than an independent benchmark.

## Future Improvements

Potential improvements for future versions include:

- Integrating an LLM-based tool-selection mechanism instead of keyword-based classification.
- Adding pagination support for repositories, issues, and pull requests.
- Expanding the evaluation dataset with more diverse natural-language queries.
- Deploying the MCP server remotely for access by multiple clients.
- Adding more read-only GitHub tools, such as commit history and file contents.

## Project Scope

This project currently focuses on read-only GitHub operations. It does not support creating, modifying, or deleting GitHub resources.