"""
Test MCP Server with different approaches
Testing FastMCP stdio transport
"""

import asyncio
import logging
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple test server
mcp = FastMCP("test-server")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone"""
    return f"Hello, {name}!"

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    logger.info("Starting test MCP server...")
    try:
        # Try running with stdio transport
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("Server exited")