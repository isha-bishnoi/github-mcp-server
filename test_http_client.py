
import asyncio
import os
import httpx

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()


async def main():
    token = os.getenv("MCP_ACCESS_TOKEN")

    if not token:
        raise RuntimeError("MCP_ACCESS_TOKEN is not configured.")

    async with httpx.AsyncClient(
    headers={"Authorization": f"Bearer {token}"},
    timeout=httpx.Timeout(120.0, connect=20.0),
) as http_client:

        async with streamable_http_client(
            "https://github-mcp-server-ide3.onrender.com/mcp",
            http_client=http_client,
        ) as (read_stream, write_stream):

            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                tools = await session.list_tools()

                result = await session.call_tool(
                    "get_repository",
                    arguments={
                        "owner": "octocat",
                        "repo": "Hello-World"
                    }
                )

                repositories = await session.call_tool(
                    "list_repositories",
                    arguments={
                        "owner": "octocat"
                    }
                )

                issues = await session.call_tool(
                    "list_issues",
                    arguments={
                        "owner": "octocat",
                        "repo": "Hello-World",
                        "state": "open"
                    }
                )

                pull_requests = await session.call_tool(
    "list_pull_requests",
    arguments={
        "owner": "octocat",
        "repo": "Hello-World",
        "state": "open"
    }
)

                print("\nRepository details:")
                print(result.content)

                print("\nConnected to GitHub MCP Server!")
                print("\nAvailable tools:")

                print("\nRepository list:")
                print(repositories.content[:1])

                print("\nIssues:")
                print(issues.content[:1])

                print("\nPull requests:")
                print(pull_requests.content[:1])

                for tool in tools.tools:
                    print(f"- {tool.name}")




if __name__ == "__main__":
    asyncio.run(main())
