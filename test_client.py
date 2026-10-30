
import asyncio
import os
import sys

from mcp import Client, StdioServerParameters


async def main():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "github_mcp.server"],
        env=os.environ.copy(),
    )

    async with Client(server) as client:
        tools = await client.list_tools()
        print("Available tools:", [tool.name for tool in tools.tools])

        result = await client.call_tool(
            "get_repository",
            {"owner": "octocat", "repo": "Hello-World"},
        )
        print("\nRepository result:", result)

        result = await client.call_tool(
            "list_repositories",
            {"owner": "octocat"},
        )
        print("\nList repositories result:", result)

        result = await client.call_tool(
            "list_issues",
            {
                "owner": "octocat",
                "repo": "Hello-World",
                "state": "open",
            },
        )
        print("\nList issues result:", result)

        result = await client.call_tool(
            "list_pull_requests",
            {
                "owner": "octocat",
                "repo": "Hello-World",
                "state": "open",
            },
        )
        print("\nList pull requests result:", result)


if __name__ == "__main__":
    asyncio.run(main())
