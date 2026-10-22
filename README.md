# MCP Git Sentinel 🛡️

[![CI](https://github.com/Sir-Lancelot-du-Lac-Dev/mcp-git-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/Sir-Lancelot-du-Lac-Dev/mcp-git-sentinel/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-brightgreen)](https://www.python.org/)
[![MCP Standard](https://img.shields.io/badge/MCP-2024--11--05-blueviolet)](https://modelcontextprotocol.io/)

A high-performance, zero-dependency **Model Context Protocol (MCP)** server engineered to solve **Agent Context Economics**: protecting LLM context windows from diff explosion, filtering repository noise, extracting AST semantic outlines, and intercepting accidental secret leakage before code reaches AI models.

---

## 💡 The Thesis: Agent Context Economics

In modern autonomous software engineering, AI Coding Agents (such as OpenAI Codex, Claude Code, Cursor, and Windsurf) rely on context windows as their primary working memory. However, traditional Git was built for human terminal readers and disk storage�?*not for token-metered neural attention windows**.

This architectural mismatch creates three critical bottlenecks:

1. **The Context Explosion Dilemma**:
   Updating a single package in `package.json` often dumps **10,000+ lines** of lockfile diffs (`package-lock.json`, `pnpm-lock.yaml`, `Cargo.lock`), consuming **30,000 to 60,000 tokens** in a single tool call. This causes immediate context exhaustion, slows generation, and costs dollars per query.
2. **Attention Degradation (Needle in a Haystack)**:
   When prompt context is inundated with minified bundles (`.min.js`), source maps (`.map`), and hash churn, LLMs lose sensitivity to critical business logic modifications and security regressions.
3. **The Upstream Secret Leakage Hazard**:
   Agents analyzing unstaged code or automated PR workflows risk ingesting unmasked API keys (`sk-...`, `ghp_...`, AWS secrets) directly into model prompt logs.

---

## 🚀 The Solution: Architecture & Core Pillars

`mcp-git-sentinel` sits as an intelligent semantic proxy between Git and your LLM Agent:

```
┌──────────────�?     JSON-RPC 2.0 / stdio      ┌─────────────────────────────────�?     git cli      ┌──────────────�?
�? AI Agent    �?◄────────────────────────────�?�?       mcp-git-sentinel         �?◄───────────────�?�? Local Repo  �?
�?(Codex/MCP)  �?                               �?(Zero External Runtime Deps)    �?                  �?             �?
└──────────────�?                               └────────────────┬────────────────�?                  └──────────────�?
                                                                 �?
                                     ┌───────────────────────────┴───────────────────────────�?
                                     �?                                                      �?
                           ┌─────────▼─────────�?   ┌─────────────────▼─────────�?  ┌────────▼────────�?
                           �?Noise Suppression �?   �?Shannon Entropy Sentinel  �?  �? AST Semantic   �?
                           �?14+ Lockfile types�?   �?H(X) secret calculation   �?  �? Outline Parser �?
                           �?Minified / Maps   �?   �?Pattern & Masking Engine  �?  �? Class/Def Sig  �?
                           └───────────────────�?   └───────────────────────────�?  └─────────────────�?
```

### 1. AST-Aware Semantic Change Outlines
Rather than dumping 500 lines of implementation diffs, `mcp-git-sentinel` parses Python, TypeScript, and Go AST signatures to tell the model *what changed structurally* before presenting diff lines:
> `[CLASS] class PaymentProcessor` -> `[FUNC] def process(amount: float, currency: str)`

### 2. Zero-Overhead Shannon Entropy Secret Guard
Using pure information theory mathematics, the server computes character randomness in real time:
$$H(X) = -\sum_{i=1}^{n} P(x_i) \log_2 P(x_i)$$
Natural code registers between $2.0 - 3.5$. High-entropy strings ($H \ge 4.4$) and modern AI credentials (`sk-proj-...`, `ghp_...`, AWS keys) trigger an immediate **`🚨 SECURITY ALERT`** and automatic masking before the diff ever leaves your machine.

### 3. In-Memory 3-Way Merge Simulation (`git merge-tree`)
Simulates branch compatibility in-memory without checking out branches, modifying files, or creating dirty `<<<<<<< HEAD` conflict markers on disk.

---

## 🛠�?MCP Tools Exposed

| Tool | Description |
| :--- | :--- |
| **`smart_diff`** | Generates token-budgeted, noise-filtered diffs with AST outlines and secret leak detection. |
| **`scan_secrets`** | Audits unstaged/staged changes specifically for high-entropy tokens and credential leaks. |
| **`inspect_branch`** | Inspects current branch topology, uncommitted counts, upstream divergence, and recent commits. |
| **`detect_conflicts`** | In-memory 3-way merge conflict check against a target branch (e.g. `main`). |
| **`estimate_context_cost`** | Analyzes working tree modifications and breaks down token usage and noise bloat file-by-file. |

---

## �?Quick Start

### Installation

```bash
# Clone the repository
git clone git@github.com:Sir-Lancelot-du-Lac-Dev/mcp-git-sentinel.git
cd mcp-git-sentinel

# Install in editable mode
pip install -e .
```

Or run directly without installation (uses only Python standard library):
```bash
python -m mcp_git_sentinel.cli
```

---

## 🔌 Configuration

### 1. Cursor / Windsurf (`mcp.json`)
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

## 🧪 Testing & Quality Assurance

Run the comprehensive unit test suite:
```bash
pytest -v
```
All 18 unit tests run in **< 2.5 seconds** and validate cross-platform compatibility across Ubuntu, Windows, and macOS on Python 3.10, 3.11, and 3.12.

---

## 📜 License

Distributed under the [MIT License](LICENSE).
Copyright (c) 2026 Sir-Lancelot-du-Lac-Dev.
