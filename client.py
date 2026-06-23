import asyncio
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class ResumeMCPClient:
    """Synchronous wrapper for MCP client to be used safely inside Streamlit."""
    
    def __init__(self):
        server_path = os.path.join(os.path.dirname(__file__), "server.py")
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_path],
            env=os.environ.copy()
        )

    async def _call_tool(self, name: str, args: dict) -> str:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments=args)
                if result.isError:
                    raise Exception(result.content[0].text)
                return result.content[0].text

    def call(self, name: str, args: dict) -> dict:
        """Calls an MCP tool synchronously and returns parsed JSON."""
        result_str = asyncio.run(self._call_tool(name, args))
        return json.loads(result_str)
