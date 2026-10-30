
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    async with streamable_http_client(
        "http://localhost:8000/mcp"
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

            print("\nRepository details:")
            print(result.content)

            print("Connected to GitHub MCP Server!")
            print("\nAvailable tools:")

            for tool in tools.tools:
                print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())
