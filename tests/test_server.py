"""Unit tests for JSON-RPC 2.0 MCP server handlers."""

import pytest
from src.mcp_git_sentinel.server import MCPServer


@pytest.fixture
def server():
    return MCPServer()


def test_server_initialize(server):
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    resp = server.handle_request(req)
    assert resp["id"] == 1
    assert "capabilities" in resp["result"]
    assert resp["result"]["serverInfo"]["name"] == "mcp-git-sentinel"


def test_server_tools_list(server):
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    resp = server.handle_request(req)
    assert resp["id"] == 2
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]

    assert "inspect_branch" in tool_names
    assert "smart_diff" in tool_names
    assert "scan_secrets" in tool_names
    assert "detect_conflicts" in tool_names
    assert "estimate_context_cost" in tool_names


def test_server_ping(server):
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "ping"
    }
    resp = server.handle_request(req)
    assert resp["id"] == 3
    assert resp["result"] == {}


def test_server_unknown_method(server):
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "non_existent_method"
    }
    resp = server.handle_request(req)
    assert resp["id"] == 4
    assert "error" in resp
    assert resp["error"]["code"] == -32601
