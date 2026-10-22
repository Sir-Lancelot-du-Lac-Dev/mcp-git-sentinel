"""Intelligent noise detection and filtering engine for Git changes."""

import os
import re
from typing import Set

# Canonical lockfiles that introduce massive diff noise
KNOWN_LOCKFILES: Set[str] = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pnpm-lock.yml",
    "poetry.lock",
    "cargo.lock",
    "gemfile.lock",
    "composer.lock",
    "packages.lock.json",
    "go.sum",
    "pipfile.lock",
    "uv.lock",
    "bun.lockb",
}

# Suffixes typically representing compiled, minified, or binary code
NOISY_EXTENSIONS: Set[str] = {
    ".min.js",
    ".min.css",
    ".bundle.js",
    ".chunk.js",
    ".map",
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".dylib",
    ".exe",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".svg",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".7z",
    ".rar",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".db",
    ".sqlite",
    ".sqlite3",
}

# Directory prefixes that represent build outputs or external vendor packages
NOISY_DIR_PREFIXES = (
    "node_modules/",
    "dist/",
    "build/",
    "out/",
    "target/",
    "vendor/",
    ".next/",
    ".nuxt/",
    ".pytest_cache/",
    "__pycache__/",
    ".venv/",
    "env/",
    "venv/",
)


class NoiseFilter:
    """Detects whether a modified file should be treated as diff noise."""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize path separators for consistent matching."""
        return path.replace("\\", "/").strip()

    @classmethod
    def is_noisy(cls, filepath: str) -> bool:
        """Determine if a file path is considered noise for LLM context windows."""
        norm_path = cls.normalize_path(filepath)
        filename = os.path.basename(norm_path).lower()

        # 1. Exact lockfile match
        if filename in KNOWN_LOCKFILES:
            return True

        # 2. Noisy directory prefix
        for prefix in NOISY_DIR_PREFIXES:
            if norm_path.startswith(prefix) or f"/{prefix}" in f"/{norm_path}":
                return True

        # 3. Noisy extension match
        lower_path = norm_path.lower()
        for ext in NOISY_EXTENSIONS:
            if lower_path.endswith(ext):
                return True

        # 4. Large auto-generated / minified patterns
        if re.search(r"[-._]min\.(js|css)$", lower_path):
            return True

        return False

    @staticmethod
    def get_file_priority(filepath: str) -> int:
        """
        Calculates semantic importance for ranking diff inclusion.
        Higher integer = higher priority for LLM attention.
        """
        path = filepath.lower()

        # Primary source code files
        if any(path.endswith(ext) for ext in [".py", ".rs", ".go", ".ts", ".tsx", ".js", ".jsx", ".c", ".cpp", ".h", ".cs", ".java", ".rb"]):
            if "test" in path or "spec" in path:
                return 70  # Tests are important, but core logic comes first
            return 100

        # Architecture & Documentation
        if any(path.endswith(ext) for ext in [".md", ".rst", ".adoc"]):
            return 60

        # Configuration & Schemas
        if any(path.endswith(ext) for ext in [".toml", ".yaml", ".yml", ".json", ".xml", ".env.example"]):
            return 50

        # Everything else
        return 30
