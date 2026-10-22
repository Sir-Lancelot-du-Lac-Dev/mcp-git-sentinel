"""JSON-RPC 2.0 Stdio Model Context Protocol (MCP) Server Implementation."""

import json
import sys
from typing import Dict, Any, Optional
from .core.git_inspector import GitInspector, GitExecutionError
from .core.diff_analyzer import DiffAnalyzer
from .core.noise_filter import NoiseFilter


class MCPServer:
    """Zero-dependency Model Context Protocol stdio server for Git Sentinel."""

    SERVER_NAME = "mcp-git-sentinel"
    SERVER_VERSION = "0.1.0"
    PROTOCOL_VERSION = "2024-11-05"

    def __init__(self, repo_path: Optional[str] = None):
        self.inspector = GitInspector(repo_path)

    def get_tool_definitions(self) -> list:
        """Return MCP tool schemas."""
        return [
            {
                "name": "inspect_branch",
                "description": "Inspects current Git branch topology, uncommitted file counts, upstream divergence, and recent commit history.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "smart_diff",
                "description": "Generates a token-budgeted, noise-filtered semantic git diff for LLM context windows (auto-filtering lockfiles, dist, and minified bundles).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target_ref": {
                            "type": "string",
                            "description": "Git revision or branch to diff against (e.g. 'HEAD~1', 'origin/main'). Defaults to working tree diff.",
                            "default": ""
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Strict token ceiling for the diff output (default: 4000).",
                            "default": 4000
                        },
                        "filter_noise": {
                            "type": "boolean",
                            "description": "Whether to automatically discard lockfiles and generated assets (default: true).",
                            "default": True
                        },
                        "staged_only": {
                            "type": "boolean",
                            "description": "Whether to only diff staged files (git diff --cached).",
                            "default": False
                        }
                    }
                }
            },
            {
                "name": "detect_conflicts",
                "description": "Performs an in-memory 3-way merge simulation against a target branch to detect potential merge conflicts before merging.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target_ref": {
                            "type": "string",
                            "description": "Target branch or ref to test mergeability against (e.g. 'main', 'origin/main').",
                            "default": "main"
                        }
                    },
                    "required": ["target_ref"]
                }
            },
            {
                "name": "estimate_context_cost",
                "description": "Analyzes pending working tree changes and breaks down estimated LLM token consumption file-by-file.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "staged_only": {
                            "type": "boolean",
                            "description": "Whether to analyze only staged changes.",
                            "default": False
                        }
                    }
                }
            }
        ]

    def handle_tool_call(self, name: str, args: Dict[str, Any]) -> str:
        """Route tool invocation to appropriate handler."""
        if name == "inspect_branch":
            status = self.inspector.get_branch_status()
            recent_str = "\n".join([f"  - `{c['hash']}` {c['subject']} ({c['author']}, {c['relative_time']})" for c in status.recent_commits])
            return (
                f"### Branch Inspection Report\n"
                f"- **Current Branch:** `{status.current_branch}`\n"
                f"- **Upstream:** `{status.upstream_branch or 'None'}` (Ahead: {status.ahead}, Behind: {status.behind})\n"
                f"- **Working Tree Status:** Staged: {status.staged_count}, Unstaged: {status.unstaged_count}, Untracked: {status.untracked_count}\n"
                f"- **Recent Commits:**\n{recent_str or '  (No commit history)'}"
            )

        elif name == "smart_diff":
            target_ref = args.get("target_ref", "")
            max_tokens = args.get("max_tokens", 4000)
            filter_noise = args.get("filter_noise", True)
            staged_only = args.get("staged_only", False)

            raw_diff = self.inspector.get_raw_diff(target_ref=target_ref or None, staged_only=staged_only)
            result = DiffAnalyzer.analyze_smart_diff(
                raw_diff=raw_diff,
                target_ref=target_ref or ("staged index" if staged_only else "working tree"),
                max_tokens=max_tokens,
                filter_noise=filter_noise
            )
            return result.formatted_diff

        elif name == "detect_conflicts":
            target_ref = args.get("target_ref", "main")
            res = self.inspector.detect_merge_conflicts(target_ref)
            if not res.has_conflicts:
                return f"✅ **Clean Merge:** No merge conflicts detected with `{target_ref}`."
            else:
                files_str = "\n".join([f"- `{f}`" for f in res.conflict_files])
                return (
                    f"⚠️ **Merge Conflict Warning:** Target ref `{target_ref}` has conflicts:\n"
                    f"{files_str}\n\n"
                    f"**Details:**\n```\n{res.raw_details}\n```"
                )

        elif name == "estimate_context_cost":
            staged_only = args.get("staged_only", False)
            raw_diff = self.inspector.get_raw_diff(staged_only=staged_only)
            summaries = DiffAnalyzer.parse_unified_diff(raw_diff)

            if not summaries:
                return "ℹ️ No changes found in working tree to estimate."

            total_tokens = sum(s.estimated_tokens for s in summaries)
            noisy_tokens = sum(s.estimated_tokens for s in summaries if s.is_noisy)

            lines = [
                f"# Context Window Expenditure Estimate",
                f"- **Total Raw Tokens:** ~{total_tokens} tokens",
                f"- **Noisy Bloat Tokens:** ~{noisy_tokens} tokens ({(noisy_tokens / (total_tokens or 1) * 100):.1f}% of total diff)",
                f"\n| File | Status | Lines (+/-) | Estimated Tokens | Noise Flag |",
                f"| :--- | :--- | :--- | :--- | :--- |"
            ]
            for s in sorted(summaries, key=lambda x: x.estimated_tokens, reverse=True):
                flag = "🚫 Noise" if s.is_noisy else "✅ Clean"
                lines.append(f"| `{s.path}` | {s.status} | +{s.additions}/-{s.deletions} | ~{s.estimated_tokens} | {flag} |")

            return "\n".join(lines)

        else:
            raise ValueError(f"Unknown tool name: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming JSON-RPC 2.0 messages."""
        msg_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": self.SERVER_NAME,
                        "version": self.SERVER_VERSION
                    }
                }
            }

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": self.get_tool_definitions()
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                content = self.handle_tool_call(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": content
                            }
                        ]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    }
                }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        else:
            if msg_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            return None

    def run_stdio(self):
        """Standard stdio event loop."""
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp:
                    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
