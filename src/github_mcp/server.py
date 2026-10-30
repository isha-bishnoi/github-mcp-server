
import asyncio
import os

import httpx
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

mcp = MCPServer("GitHub Read-Only MCP Server")


async def github_get(
    url: str,
    headers: dict,
    params: dict | None = None,
) -> dict | list:
    """Make a GitHub GET request with retries for transient failures."""
    async with httpx.AsyncClient(timeout=10) as client:
        for attempt in range(3):
            try:
                if params is None:
                    response = await client.get(
                        url,
                        headers=headers,
                    )
                else:
                    response = await client.get(
                        url,
                        headers=headers,
                        params=params,
                    )

                # Retry server errors (HTTP 5xx).
                if response.status_code >= 500 and attempt < 2:
                    await asyncio.sleep(1)
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                if attempt == 2:
                    raise
                await asyncio.sleep(1)

            except httpx.RequestError:
                if attempt == 2:
                    raise
                await asyncio.sleep(1)

    raise RuntimeError("GitHub request failed after three attempts.")


def get_github_headers() -> dict:
    """Build headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-read-only-mcp-server",
    }

    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def format_http_error(exc: httpx.HTTPStatusError) -> str:
    """Convert GitHub HTTP errors into readable messages."""
    status = exc.response.status_code

    if status == 403:
        return "GitHub access forbidden or API rate limit exceeded."

    return f"GitHub API returned HTTP {status}."


def format_request_error(exc: httpx.RequestError) -> str:
    """Convert network errors into readable messages."""
    if isinstance(exc, httpx.TimeoutException):
        return "Request to GitHub timed out."

    return "Could not connect to GitHub."


@mcp.tool()
async def get_repository(owner: str, repo: str) -> dict:
    """Get basic details about a public GitHub repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = get_github_headers()

    try:
        data = await github_get(url, headers)

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {"error": f"Repository '{owner}/{repo}' not found."}
        return {"error": format_http_error(exc)}

    except httpx.RequestError as exc:
        return {"error": format_request_error(exc)}

    return {
        "full_name": data["full_name"],
        "description": data["description"],
        "default_branch": data["default_branch"],
        "stars": data["stargazers_count"],
        "open_issues": data["open_issues_count"],
        "html_url": data["html_url"],
    }


@mcp.tool()
async def list_repositories(owner: str) -> list[dict]:
    """List public repositories belonging to a GitHub user or organization."""
    url = f"https://api.github.com/users/{owner}/repos"
    headers = get_github_headers()

    try:
        data = await github_get(
            url,
            headers,
            params={"per_page": 100, "sort": "updated"},
        )

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return [
                {"error": f"GitHub user or organization '{owner}' not found."}
            ]
        return [{"error": format_http_error(exc)}]

    except httpx.RequestError as exc:
        return [{"error": format_request_error(exc)}]

    return [
        {
            "name": repository["name"],
            "full_name": repository["full_name"],
            "description": repository["description"],
            "stars": repository["stargazers_count"],
            "url": repository["html_url"],
        }
        for repository in data
    ]


@mcp.tool()
async def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
) -> list[dict]:
    """List repository issues filtered by state: open, closed, or all."""
    if state not in {"open", "closed", "all"}:
        return [
            {"error": "Invalid state. Choose 'open', 'closed', or 'all'."}
        ]

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = get_github_headers()

    try:
        data = await github_get(
            url,
            headers,
            params={"state": state, "per_page": 100},
        )

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return [{"error": f"Repository '{owner}/{repo}' not found."}]
        return [{"error": format_http_error(exc)}]

    except httpx.RequestError as exc:
        return [{"error": format_request_error(exc)}]

    return [
        {
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "url": issue["html_url"],
            "created_at": issue["created_at"],
        }
        for issue in data
        if "pull_request" not in issue
    ]


@mcp.tool()
async def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
) -> list[dict]:
    """List pull requests filtered by state: open, closed, or all."""
    if state not in {"open", "closed", "all"}:
        return [
            {"error": "Invalid state. Choose 'open', 'closed', or 'all'."}
        ]

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = get_github_headers()

    try:
        data = await github_get(
            url,
            headers,
            params={"state": state, "per_page": 100},
        )

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return [{"error": f"Repository '{owner}/{repo}' not found."}]
        return [{"error": format_http_error(exc)}]

    except httpx.RequestError as exc:
        return [{"error": format_request_error(exc)}]

    return [
        {
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "url": pr["html_url"],
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
        }
        for pr in data
    ]


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
        )
    else:
        mcp.run(transport="stdio")
