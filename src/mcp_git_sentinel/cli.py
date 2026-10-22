"""Command line interface for MCP Git Sentinel."""

import argparse
import sys
from . import __version__
from .server import MCPServer


def main():
    parser = argparse.ArgumentParser(
        prog="mcp-git-sentinel",
        description="High-performance Model Context Protocol (MCP) server for Git diff analysis and context window protection."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        default=None,
        help="Custom target repository path (defaults to current working directory)."
    )

    args = parser.parse_args()

    server = MCPServer(repo_path=args.repo_path)
    server.run_stdio()


if __name__ == "__main__":
    main()
