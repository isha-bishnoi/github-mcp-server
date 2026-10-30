
import httpx
import pytest

from github_mcp.server import get_repository
from github_mcp.server import MCPAuthMiddleware

@pytest.mark.anyio
async def test_mcp_auth_missing_token():
    async def mock_app(scope, receive, send):
        pass

    middleware = MCPAuthMiddleware(mock_app, "test-secret")

    scope = {
        "type": "http",
        "path": "/mcp",
        "headers": [],
    }

    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await middleware(scope, receive, send)

    assert messages[0]["status"] == 401

@pytest.mark.anyio
async def test_mcp_auth_invalid_token():
    async def mock_app(scope, receive, send):
        pass

    middleware = MCPAuthMiddleware(mock_app, "correct-secret")

    scope = {
        "type": "http",
        "path": "/mcp",
        "headers": [
            (b"authorization", b"Bearer wrong-secret"),
        ],
    }

    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await middleware(scope, receive, send)

    assert messages[0]["status"] == 401

@pytest.mark.anyio
async def test_mcp_auth_valid_token():
    app_called = False

    async def mock_app(scope, receive, send):
        nonlocal app_called
        app_called = True

    middleware = MCPAuthMiddleware(mock_app, "correct-secret")

    scope = {
        "type": "http",
        "path": "/mcp",
        "headers": [
            (b"authorization", b"Bearer correct-secret"),
        ],
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        pass

    await middleware(scope, receive, send)

    assert app_called is True

@pytest.mark.anyio
async def test_get_repository_success(monkeypatch):
    async def mock_get(self, url, headers=None):
        return httpx.Response(
            200,
            json={
                "full_name": "octocat/Hello-World",
                "description": "Test repository",
                "default_branch": "master",
                "stargazers_count": 100,
                "open_issues_count": 5,
                "html_url": "https://github.com/octocat/Hello-World",
            },
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await get_repository("octocat", "Hello-World")

    assert result["full_name"] == "octocat/Hello-World"
    assert result["stars"] == 100
    assert result["open_issues"] == 5


@pytest.mark.anyio
async def test_get_repository_retries_after_server_error(monkeypatch):
    calls = 0

    async def mock_get(self, url, headers=None):
        nonlocal calls
        calls += 1

        if calls == 1:
            status = 500
        else:
            status = 200

        data = {
            "full_name": "octocat/Hello-World",
            "description": "Test repository",
            "default_branch": "master",
            "stargazers_count": 100,
            "open_issues_count": 5,
            "html_url": "https://github.com/octocat/Hello-World",
        }

        return httpx.Response(
            status,
            json=data if status == 200 else None,
            request=httpx.Request("GET", url),
        )

    async def no_wait(seconds):
        pass

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr("github_mcp.server.asyncio.sleep", no_wait)

    result = await get_repository("octocat", "Hello-World")

    assert result["full_name"] == "octocat/Hello-World"
    assert calls == 2


@pytest.mark.anyio
async def test_get_repository_stops_after_three_attempts(monkeypatch):
    calls = 0

    async def mock_get(self, url, headers=None):
        nonlocal calls
        calls += 1

        return httpx.Response(
            500,
            request=httpx.Request("GET", url),
        )

    async def no_wait(seconds):
        pass

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr("github_mcp.server.asyncio.sleep", no_wait)

    result = await get_repository("octocat", "Hello-World")

    assert calls == 3
    assert result == {
    "error": (
        "GitHub API returned HTTP 500. "
        "Message: . "
        "Rate limit remaining: unknown. "
        "Resource: unknown."
    )
}


@pytest.mark.anyio
async def test_get_repository_not_found(monkeypatch):
    calls = 0

    async def mock_get(self, url, headers=None):
        nonlocal calls
        calls += 1

        return httpx.Response(
            404,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await get_repository("fake-owner", "fake-repo")

    assert result == {
        "error": "Repository 'fake-owner/fake-repo' not found."
    }
    assert calls == 1


@pytest.mark.anyio
async def test_list_repositories_success(monkeypatch):
    async def mock_get(self, url, headers=None, params=None):
        return httpx.Response(
            200,
            json=[
                {
                    "name": "Hello-World",
                    "full_name": "octocat/Hello-World",
                    "description": "Test repository",
                    "stargazers_count": 100,
                    "html_url": "https://github.com/octocat/Hello-World",
                }
            ],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    from github_mcp.server import list_repositories

    result = await list_repositories("octocat")

    assert len(result) == 1
    assert result[0]["full_name"] == "octocat/Hello-World"
    assert result[0]["stars"] == 100

@pytest.mark.anyio
async def test_list_issues_success(monkeypatch):
    async def mock_get(self, url, headers=None, params=None):
        return httpx.Response(
            200,
            json=[
                {
                    "number": 123,
                    "title": "Test issue",
                    "state": "open",
                    "html_url": "https://github.com/octocat/Hello-World/issues/123",
                    "created_at": "2026-01-01T00:00:00Z",
                },
                {
                    "number": 124,
                    "title": "Test pull request",
                    "state": "open",
                    "html_url": "https://github.com/octocat/Hello-World/pull/124",
                    "created_at": "2026-01-02T00:00:00Z",
                    "pull_request": {
                        "url": "https://api.github.com/repos/octocat/Hello-World/pulls/124"
                    },
                },
            ],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    from github_mcp.server import list_issues

    result = await list_issues("octocat", "Hello-World")

    assert len(result) == 1
    assert result[0]["number"] == 123
    assert result[0]["title"] == "Test issue"
    assert result[0]["state"] == "open"


@pytest.mark.anyio
async def test_list_pull_requests_success(monkeypatch):
    async def mock_get(self, url, headers=None, params=None):
        return httpx.Response(
            200,
            json=[
                {
                    "number": 42,
                    "title": "Add documentation",
                    "state": "open",
                    "html_url": "https://github.com/octocat/Hello-World/pull/42",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-02T00:00:00Z",
                }
            ],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    from github_mcp.server import list_pull_requests

    result = await list_pull_requests("octocat", "Hello-World")

    assert len(result) == 1
    assert result[0]["number"] == 42
    assert result[0]["title"] == "Add documentation"
    assert result[0]["state"] == "open"


@pytest.mark.anyio
async def test_list_pull_requests_not_found(monkeypatch):
    async def mock_get(self, url, headers=None, params=None):
        return httpx.Response(
            404,
            json={"message": "Not Found"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    from github_mcp.server import list_pull_requests

    result = await list_pull_requests("octocat", "nonexistent-repo")

    assert len(result) == 1
    assert "error" in result[0]


@pytest.mark.anyio
async def test_list_pull_requests_connection_error(monkeypatch):
    async def mock_get(self, url, headers=None, params=None):
        raise httpx.ConnectError(
            "Connection failed",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    from github_mcp.server import list_pull_requests

    result = await list_pull_requests("octocat", "Hello-World")

    assert result == [{"error": "Could not connect to GitHub."}]


@pytest.mark.anyio
async def test_list_pull_requests_retries_after_server_error(monkeypatch):
    calls = 0

    async def mock_get(self, url, headers=None, params=None):
        nonlocal calls
        calls += 1

        if calls == 1:
            status = 500
        else:
            status = 200

        data = [
            {
                "number": 42,
                "title": "Add documentation",
                "state": "open",
                "html_url": "https://github.com/octocat/Hello-World/pull/42",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
            }
        ]

        return httpx.Response(
            status,
            json=data if status == 200 else None,
            request=httpx.Request("GET", url),
        )

    async def no_wait(seconds):
        pass

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr("github_mcp.server.asyncio.sleep", no_wait)

    from github_mcp.server import list_pull_requests

    result = await list_pull_requests("octocat", "Hello-World")

    assert calls == 2
    assert result[0]["number"] == 42
    assert result[0]["title"] == "Add documentation"


import pytest
from github_mcp.server import list_issues


@pytest.mark.anyio
async def test_list_issues_invalid_state():
    result = await list_issues(
        owner="octocat",
        repo="Hello-World",
        state="invalid",
    )

    assert result == [
        {"error": "Invalid state. Choose 'open', 'closed', or 'all'."}
    ]


@pytest.mark.anyio
async def test_get_repository_forbidden(monkeypatch):
    import httpx
    from github_mcp.server import get_repository

    async def mock_get(self, url, headers=None):
        request = httpx.Request("GET", url)
        response = httpx.Response(403, request=request)
        raise httpx.HTTPStatusError(
            "Forbidden",
            request=request,
            response=response,
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await get_repository("octocat", "Hello-World")

    assert result == {
    "error": (
        "GitHub API returned HTTP 403. "
        "Message: . "
        "Rate limit remaining: unknown. "
        "Resource: unknown."
    )
}


@pytest.mark.anyio
async def test_get_repository_not_found(monkeypatch):
    import httpx
    from github_mcp.server import get_repository

    async def mock_get(self, url, headers=None):
        request = httpx.Request("GET", url)
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError(
            "Not Found",
            request=request,
            response=response,
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await get_repository("unknown-owner", "unknown-repo")

    assert result == {
        "error": "Repository 'unknown-owner/unknown-repo' not found."
    }


@pytest.mark.anyio
async def test_list_repositories_not_found(monkeypatch):
    import httpx
    from github_mcp.server import list_repositories

    async def mock_get(self, url, headers=None, params=None):
        request = httpx.Request("GET", url)
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError(
            "Not Found",
            request=request,
            response=response,
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await list_repositories("unknown-owner")

    assert result == [
        {"error": "GitHub user or organization 'unknown-owner' not found."}
    ]


@pytest.mark.anyio
async def test_list_issues_not_found(monkeypatch):
    import httpx
    from github_mcp.server import list_issues

    async def mock_get(self, url, headers=None, params=None):
        request = httpx.Request("GET", url)
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError(
            "Not Found",
            request=request,
            response=response,
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await list_issues("octocat", "unknown-repo")

    assert result == [
        {"error": "Repository 'octocat/unknown-repo' not found."}
    ]


@pytest.mark.anyio
async def test_list_pull_requests_invalid_state():
    from github_mcp.server import list_pull_requests

    result = await list_pull_requests(
        owner="octocat",
        repo="Hello-World",
        state="invalid",
    )

    assert result == [
        {"error": "Invalid state. Choose 'open', 'closed', or 'all'."}
    ]


@pytest.mark.anyio
async def test_list_issues_connection_error(monkeypatch):
    import httpx
    from github_mcp.server import list_issues

    async def mock_get(self, url, headers=None, params=None):
        raise httpx.ConnectError(
            "Connection failed",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await list_issues("octocat", "Hello-World")

    assert result == [
        {"error": "Could not connect to GitHub."}
    ]

@pytest.mark.anyio
async def test_list_repositories_connection_error(monkeypatch):
    import httpx
    from github_mcp.server import list_repositories

    async def mock_get(self, url, headers=None, params=None):
        raise httpx.ConnectError(
            "Connection failed",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await list_repositories("octocat")

    assert result == [
        {"error": "Could not connect to GitHub."}
    ]

@pytest.mark.anyio
async def test_list_pull_requests_timeout(monkeypatch):
    import httpx
    from github_mcp.server import list_pull_requests

    async def mock_get(self, url, headers=None, params=None):
        raise httpx.TimeoutException(
            "Request timed out",
            request=httpx.Request("GET", url),
        )

    async def no_wait(seconds):
        pass

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr("github_mcp.server.asyncio.sleep", no_wait)

    result = await list_pull_requests("octocat", "Hello-World")

    assert result == [{"error": "Request to GitHub timed out."}]


@pytest.mark.anyio
async def test_get_repository_timeout(monkeypatch):
    import httpx
    from github_mcp.server import get_repository

    calls = 0

    async def mock_get(self, url, headers=None):
        nonlocal calls
        calls += 1
        raise httpx.TimeoutException(
            "Request timed out",
            request=httpx.Request("GET", url),
        )

    async def no_wait(seconds):
        pass

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr("github_mcp.server.asyncio.sleep", no_wait)

    result = await get_repository("octocat", "Hello-World")

    assert calls == 3
    assert result == {"error": "Request to GitHub timed out."}


@pytest.mark.anyio
async def test_list_repositories_timeout(monkeypatch):
    import httpx
    from github_mcp.server import list_repositories

    calls = 0

    async def mock_get(self, url, headers=None, params=None):
        nonlocal calls
        calls += 1
        raise httpx.TimeoutException(
            "Request timed out",
            request=httpx.Request("GET", url),
        )

    async def no_wait(seconds):
        pass

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr("github_mcp.server.asyncio.sleep", no_wait)

    result = await list_repositories("octocat")

    assert calls == 3
    assert result == [{"error": "Request to GitHub timed out."}]

@pytest.mark.anyio
async def test_list_issues_retries_after_server_error(monkeypatch):
    import httpx
    from github_mcp.server import list_issues

    calls = 0

    async def mock_get(self, url, headers=None, params=None):
        nonlocal calls
        calls += 1

        if calls == 1:
            return httpx.Response(
                500,
                request=httpx.Request("GET", url),
            )

        return httpx.Response(
            200,
            json=[
                {
                    "number": 123,
                    "title": "Test issue",
                    "state": "open",
                    "html_url": "https://github.com/octocat/Hello-World/issues/123",
                    "created_at": "2026-01-01T00:00:00Z",
                }
            ],
            request=httpx.Request("GET", url),
        )

    async def no_wait(seconds):
        pass

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr("github_mcp.server.asyncio.sleep", no_wait)

    result = await list_issues("octocat", "Hello-World")

    assert calls == 2
    assert result[0]["number"] == 123
    assert result[0]["title"] == "Test issue"
