"""Servidor MCP de series oficiales del BCRP."""

from fastmcp import FastMCP

mcp = FastMCP("BCRP")

if __name__ == "__main__":
    mcp.run()
