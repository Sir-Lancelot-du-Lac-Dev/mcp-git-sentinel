# MCP Git Sentinel 🛡️

[![CI](https://github.com/Chevalier-Sans-Peur/mcp-git-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/Chevalier-Sans-Peur/mcp-git-sentinel/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-brightgreen)](https://www.python.org/)
[![MCP Standard](https://img.shields.io/badge/MCP-2024--11--05-blueviolet)](https://modelcontextprotocol.io/)

A high-performance, zero-dependency **Model Context Protocol (MCP)** server engineered to protect LLM context windows from diff explosion, filter repository noise, and provide semantic branch inspection for AI coding agents (OpenAI Codex, Claude Code, Cursor, Windsurf).

---

## 🎯 The Problem

When AI coding assistants query `git diff` on real-world codebases, they frequently encounter **Context Window Bloat**:
- Modifying a single npm dependency can spit out **15,000+ lines** of changes in `package-lock.json` or `pnpm-lock.yaml`.
- Minified bundles (`.min.js`), source maps (`.map`), and build artifacts consume **40,000+ tokens** of precious context.
- **Attention Degradation**: Crucial business logic changes get drowned in boilerplate, leading to hallucinated reviews and undetected regressions.

## 🚀 The Solution: MCP Git Sentinel

`mcp-git-sentinel` acts as an intelligent proxy between Git and your LLM agent:

```
┌──────────────┐      JSON-RPC / stdio      ┌────────────────────┐      git cli      ┌──────────────┐
│  AI Agent    │ ◄────────────────────────► │  mcp-git-sentinel  │ ◄───────────────► │  Local Repo  │
│ (Codex/MCP)  │                            │                    │                   │              │
└──────────────┘                            └─────────┬──────────┘                   └──────────────┘
                                                      │
                                           ┌──────────▼──────────┐
                                           │  Noise Filter Engine│ (Filters locks, dist, maps)
                                           │  Semantic Diff Chunk│ (Ranks by AST/logic impact)
                                           │  Context Token Guard│ (Strict token budgeting)
                                           │  Pre-merge Simulator│ (3-way merge conflict check)
                                           └─────────────────────┘
```

---

## 🛠️ MCP Tools Exposed

### 1. `inspect_branch`
Inspects the current branch topology, uncommitted changes summary, and tracking upstream divergence (ahead/behind).

### 2. `smart_diff`
Generates a semantic, token-budgeted diff:
- **Noise Elimination**: Automatically excludes `package-lock.json`, `pnpm-lock.yaml`, `Cargo.lock`, `dist/`, `.map`, and binary files.
- **Token Budgeting**: Enforces strict `max_tokens` limits with truncation indicators so LLMs are never overwhelmed.
- **Priority Ranking**: Prioritizes core source code changes over docs and configurations.

### 3. `detect_conflicts`
Performs an in-memory 3-way merge simulation (`git merge-tree`) against a target branch (e.g., `main` or `origin/main`) to spot potential merge conflicts **before** attempting to merge.

### 4. `estimate_context_cost`
Analyzes pending unstaged/staged modifications and outputs a file-by-file token expenditure breakdown, flagging files that exceed safety thresholds.

---

## ⚡ Quick Start

### Installation

```bash
# Clone the repository
git clone git@github.com:Chevalier-Sans-Peur/mcp-git-sentinel.git
cd mcp-git-sentinel

# Install in editable mode
pip install -e .
```

Or run directly without installation (zero external runtime dependencies required):
```bash
python -m src.mcp_git_sentinel.cli
```

---

## 🔌 Configuration

### 1. Cursor / Windsurf
Add to your `mcp.json` configuration:
```json
{
  "mcpServers": {
    "git-sentinel": {
      "command": "python",
      "args": ["-m", "mcp_git_sentinel.cli"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### 2. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "git-sentinel": {
      "command": "python",
      "args": ["-m", "mcp_git_sentinel.cli"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### 3. OpenAI / Codex Agent CLI
```bash
codex --mcp-server "python -m mcp_git_sentinel.cli"
```

---

## 🧪 Testing

Run the comprehensive unit test suite:
```bash
pytest -v
```

---

## 📜 License

Distributed under the [MIT License](LICENSE).
Copyright (c) 2026 Chevalier-Sans-Peur.
