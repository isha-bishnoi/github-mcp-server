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
          | MCP Protocol (stdio / Streamable HTTP)
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

The MCP server supports two transport mechanisms:

- **stdio:** Used for local connections between an MCP client and the server.
- **Streamable HTTP:** Used for remote connections over HTTP, protected by bearer-token authentication.

The request flow works as follows:

1. An MCP client connects to the server using either stdio or Streamable HTTP.
2. The client discovers the tools exposed by the MCP server.
3. When a user requests GitHub information, the client invokes the appropriate tool.
4. The MCP server executes the tool and sends an asynchronous HTTP GET request to the GitHub REST API using `httpx`.
5. The server processes the API response and returns structured information to the MCP client.

The server includes retry handling and error handling for API failures, timeouts, and network issues.

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

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token
MCP_ACCESS_TOKEN=your_mcp_access_token
```

- `GITHUB_TOKEN` – Used to authenticate requests to the GitHub REST API and provide higher API rate limits.
- `MCP_ACCESS_TOKEN` – Used to protect the MCP server's Streamable HTTP endpoint with bearer-token authentication.

A GitHub personal access token is recommended. The MCP access token is required when running the server with Streamable HTTP transport.

Never commit your actual `.env` file or expose either token publicly.

## Remote Deployment

The MCP server is deployed on Render and supports remote connections using Streamable HTTP transport.

- **Platform:** Render
- **Transport:** Streamable HTTP
- **MCP Endpoint:** https://github-mcp-server-ide3.onrender.com/mcp

The HTTP endpoint is protected using bearer-token authentication. Configure the following environment variables in the deployment environment:

- `GITHUB_TOKEN` – GitHub personal access token for authenticated API requests.
- `MCP_ACCESS_TOKEN` – Secret token used to authenticate clients connecting to the MCP server.

The server requires a valid bearer token in the Authorization header when accessed over HTTP.

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

The current test suite contains **29 passing tests**.

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
- Adding more read-only GitHub tools, such as commit history and file contents.

## Project Scope

This project currently focuses on read-only GitHub operations. It does not support creating, modifying, or deleting GitHub resources.