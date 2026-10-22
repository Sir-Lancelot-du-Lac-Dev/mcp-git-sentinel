# Contributing to MCP Git Sentinel 🛡️

Thank you for your interest in contributing to **MCP Git Sentinel**! We welcome contributions that help solve **Agent Context Economics** and enhance context safety for modern AI coding agents.

---

## 🏛️ Core Architectural Principles

Before submitting code, please note our core architectural constraints:

1. **Strict Zero External Runtime Dependencies**:
   The runtime server must remain 100% dependent on the Python 3.10+ standard library (`ast`, `re`, `subprocess`, `math`, `json`, `collections`). Do not introduce external dependencies in `pyproject.toml` runtime dependencies.
2. **First-Principles Efficiency**:
   Diff parsing, Shannon entropy calculation, and AST signature extraction must complete in milliseconds to avoid blocking real-time agent tool execution loops.
3. **Cross-Platform Parity**:
   All features must work identically across Linux, Windows, and macOS without platform-specific assumptions (handle path separators and line endings cleanly).

---

## 🛠️ Development Workflow

### 1. Environment Setup
```bash
# Clone the repository
git clone git@github.com:Sir-Lancelot-du-Lac-Dev/mcp-git-sentinel.git
cd mcp-git-sentinel

# Install development dependencies
pip install -e .[dev]
```

### 2. Running Test Suite
We enforce 100% test pass rate across all matrix environments before merging:
```bash
pytest -v
```

### 3. Commit Message Conventions
We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New features or MCP tool capabilities
- `fix:` Bug fixes in diff parsing, entropy formulas, or AST traversal
- `docs:` Documentation improvements
- `perf:` Performance optimizations in token budgeting or string parsing
- `chore:` Maintenance, CI/CD, or governance updates

---

## 📥 Pull Request Lifecycle

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Write comprehensive unit tests in `tests/` covering new logic or edge cases.
3. Ensure all tests pass locally.
4. Open a Pull Request referencing relevant issues.
5. All PRs must pass the GitHub Actions CI matrix (`ubuntu-latest`, `windows-latest`, `macos-latest` on Python 3.10, 3.11, 3.12).
