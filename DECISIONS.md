# Engineering Decisions

This document captures the key engineering decisions made while building the GitHub MCP Server and the reasoning behind them.

## 1. Technology Choices

### Python

**Decision:** Use Python as the primary programming language.

**Reasoning:**
- Python has a well-supported MCP SDK.
- Its asynchronous programming capabilities make it suitable for handling API requests.
- It has a strong ecosystem for backend development and testing.

### MCP SDK

**Decision:** Use the official Python MCP SDK.

**Reasoning:**
- It provides standard MCP server functionality.
- It simplifies tool registration and communication with MCP clients.
- It avoids implementing the MCP protocol manually.

### httpx

**Decision:** Use `httpx` for communicating with the GitHub REST API.

**Reasoning:**
- Supports asynchronous HTTP requests.
- Provides timeout and exception handling.
- Works well with Python's async/await programming model.

### pytest

**Decision:** Use pytest for automated testing.

**Reasoning:**
- Supports parameterized tests.
- Makes it easy to test error handling and retry behavior.
- Helps ensure that changes do not break existing functionality.

## 2. Server Architecture Decisions

### Transport Support

**Decision:** Support both stdio and Streamable HTTP transports.

**Reasoning:**
- Stdio supports local connections between MCP clients and the server.
- Streamable HTTP enables remote MCP connections over HTTP.
- Supporting both transports makes the server usable in local and remote environments.
- The transport can be selected through environment configuration.

### HTTP Authentication

**Decision:** Protect the remote Streamable HTTP endpoint using bearer-token authentication.

**Reasoning:**
- Prevents unauthorized clients from accessing the remote MCP server.
- Uses a dedicated `MCP_ACCESS_TOKEN` environment variable.
- Keeps MCP client authentication separate from GitHub API authentication.
- Avoids hardcoding credentials in the source code.


### Read-Only Tools

**Decision:** Expose only read-only GitHub operations.

**Reasoning:**
- Prevents accidental modifications to GitHub repositories.
- Reduces security risks associated with write operations.
- Keeps the project focused on retrieving and presenting GitHub data.
- Provides a clear and limited tool interface.

### Separate Tools for Issues and Pull Requests

**Decision:** Implement `list_issues` and `list_pull_requests` as separate tools.

**Reasoning:**
- GitHub provides separate REST API endpoints for issues and pull requests.
- Separate tools make their purpose clear to MCP clients.
- GitHub's issues endpoint also returns pull requests, so the implementation explicitly filters them out.
- Separate tools make testing and error handling easier.

## 3. Reliability and Error Handling

### Retry Mechanism

**Decision:** Implement a retry mechanism for temporary GitHub API and network failures.

**Reasoning:**
- Temporary server failures may occur while communicating with the GitHub API.
- Retrying can help recover from transient network issues.
- The implementation retries HTTP 5xx responses and network-related errors.
- A maximum of three attempts prevents indefinite retrying.
- A one-second delay between attempts avoids immediately repeating failed requests.
- HTTP 403 and 404 responses are not retried because they generally require a change in permissions or resource availability.

### Request Timeouts

**Decision:** Configure a 10-second HTTP request timeout.

**Reasoning:**
- Prevents requests from waiting indefinitely.
- Helps the server handle unresponsive API requests gracefully.
- Provides predictable failure behavior.

### Error Handling

**Decision:** Handle common GitHub API and network errors explicitly.

**Reasoning:**
- HTTP 404 errors indicate that the requested resource was not found.
- HTTP 403 errors can indicate insufficient access or API rate limits.
- Timeout and connection errors are handled separately.
- User-friendly error messages make failures easier to understand and debug.

## 4. Evaluation Design

### Rule-Based Tool Selection

**Decision:** Use a keyword-based classifier to evaluate natural-language query-to-tool mapping.

**Reasoning:**
- Provides a simple and explainable baseline for tool selection.
- Does not require an external LLM API or paid service.
- Makes predictions deterministic and easy to debug.
- Allows us to measure tool-selection accuracy using predefined queries.

### Evaluation Dataset

**Decision:** Create a dataset containing 50 primary queries and 20 additional validation queries.

**Reasoning:**
- Covers different natural-language ways of requesting GitHub information.
- Tests whether queries are mapped to the correct MCP tools.
- Helps identify classification errors and improve keyword rules.

### Evaluation Metrics

**Decision:** Measure overall accuracy, per-tool accuracy, and confusion matrix.

**Reasoning:**
- Overall accuracy provides a general measure of tool-selection performance.
- Per-tool accuracy identifies weaknesses in individual tool categories.
- A confusion matrix helps identify which tools are being confused with one another.
- Failure details make incorrect predictions easier to investigate.

**Limitation:** The additional validation queries were used during classifier refinement. Therefore, their results should not be considered an independent benchmark.


### LLM-Based Tool-Calling Evaluation

**Decision:** Use the Groq API with the `qwen/qwen3.8-27b` model to evaluate LLM-based MCP tool selection and argument extraction.

**Reasoning:**
- Tests whether an LLM can select the appropriate MCP tool from natural-language requests.
- Evaluates argument extraction in addition to tool selection.
- Uses native function-calling capabilities to select tools and generate their arguments.
- Provides a comparison with the deterministic rule-based evaluation.

**Evaluation Metrics:**
- Tool-selection accuracy measures whether the expected tool was selected.
- Argument-extraction accuracy measures whether the expected arguments were generated for correctly selected tools.
- End-to-end accuracy measures whether both tool selection and argument extraction were correct.

**Results:**

The final full evaluation using 50 natural-language queries achieved:

- Tool selection: 50/50 (100%).
- Argument extraction: 50/50 (100%).
- End-to-end accuracy: 50/50 (100%).
- API errors: 0.

The model omitted the optional `state` argument in one issue query. The evaluation script normalized the missing argument to the tool's default value (`open`) before comparison, resulting in a correct match.

**Limitations:**
- The same 50-query dataset was used during tool-description and query refinement. The final score should not be treated as an independent benchmark of generalization to unseen queries.
- The evaluation measures tool selection and argument extraction, not the correctness of the actual GitHub API data returned by the tools.


## 5. Configuration and Security


### Environment Variables

**Decision:** Store credentials and configuration in environment variables, loaded through `python-dotenv` where applicable.

**Reasoning:**
- `GITHUB_TOKEN` authenticates requests to the GitHub REST API.
- `MCP_ACCESS_TOKEN` authenticates clients connecting to the remote MCP server.
- `GROQ_API_KEY` authenticates requests to the Groq API for LLM-based evaluation.
- Keeping these credentials separate follows the principle of separation of concerns.
- Prevents credentials from being hardcoded in source code.
- The `.env` file is excluded through `.gitignore`, while `.env.example` documents the required configuration using placeholders.


### Dependency Management

**Decision:** Use `pyproject.toml` to manage project metadata and dependencies.

**Reasoning:**
- Provides a centralized dependency configuration.
- Allows development dependencies to be separated from runtime dependencies.
- Pins dependency versions to reduce unexpected changes between installations.

## 6. Future Considerations

The following improvements can be considered in future versions:

- Introduce exponential backoff for retry attempts.
- Add pagination support for large GitHub API responses.
- Expand automated testing and evaluation coverage.