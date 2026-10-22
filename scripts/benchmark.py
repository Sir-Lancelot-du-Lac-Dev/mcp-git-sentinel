"""Micro-benchmark suite for MCP Git Sentinel context compression & performance."""

import sys
import time
import tracemalloc
from src.mcp_git_sentinel.core.diff_analyzer import DiffAnalyzer

def generate_synthetic_large_diff() -> str:
    """Generate a realistic 10,000-line diff with massive lockfile noise and core code."""
    chunks = []
    
    # 1. 8,000 lines of package-lock.json bloat
    chunks.append("diff --git a/package-lock.json b/package-lock.json\nindex 1111111..2222222 100644\n--- a/package-lock.json\n+++ b/package-lock.json\n")
    for i in range(8000):
        chunks.append(f'+    "@pkg/dependency-{i}": {{ "version": "2.4.{i % 10}", "resolved": "https://registry.npmjs.org/dep-{i}" }},\n')

    # 2. 1,000 lines of minified bundle noise
    chunks.append("diff --git a/dist/bundle.min.js b/dist/bundle.min.js\nindex 3333333..4444444 100644\n--- a/dist/bundle.min.js\n+++ b/dist/bundle.min.js\n")
    for i in range(1000):
        chunks.append(f'+!function(e){{var t={{}};function n(r){{if(t[r])return t[r].exports;var o=t[r]={{i:r,l:!1,exports:{{}}}}}}({i});\n')

    # 3. 80 lines of critical business logic (with class & methods)
    chunks.append("diff --git a/src/services/auth.py b/src/services/auth.py\nindex 5555555..6666666 100644\n--- a/src/services/auth.py\n+++ b/src/services/auth.py\n")
    chunks.append("+class AuthenticationService:\n+    def __init__(self, token_ttl: int = 3600):\n+        self.ttl = token_ttl\n+\n")
    for i in range(15):
        chunks.append(f"+    def verify_token_session_{i}(self, session_id: str) -> bool:\n+        return len(session_id) > 16\n")

    # 4. 40 lines of test code
    chunks.append("diff --git a/tests/test_auth.py b/tests/test_auth.py\nindex 7777777..8888888 100644\n--- a/tests/test_auth.py\n+++ b/tests/test_auth.py\n")
    for i in range(10):
        chunks.append(f"+def test_session_validation_{i}():\n+    assert True\n")

    return "".join(chunks)

def run_benchmark():
    raw_diff = generate_synthetic_large_diff()
    raw_lines = len(raw_diff.splitlines())
    raw_tokens = DiffAnalyzer.estimate_tokens(raw_diff)

    # Warmup
    _ = DiffAnalyzer.analyze_smart_diff(raw_diff, target_ref="HEAD", max_tokens=4000)

    # Memory Tracking
    tracemalloc.start()
    start_time = time.perf_counter()
    iterations = 20
    for _ in range(iterations):
        result = DiffAnalyzer.analyze_smart_diff(
            raw_diff=raw_diff,
            target_ref="HEAD",
            max_tokens=4000,
            filter_noise=True,
            scan_secrets=True
        )
    elapsed_total = time.perf_counter() - start_time
    avg_latency_ms = (elapsed_total / iterations) * 1000.0
    _, peak_mem_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mem_mb = peak_mem_bytes / (1024 * 1024)

    sentinel_tokens = result.total_estimated_tokens
    reduction_pct = ((raw_tokens - sentinel_tokens) / raw_tokens) * 100.0

    print("=" * 65)
    print("      MCP Git Sentinel - Context Economics Micro-Benchmark      ")
    print("=" * 65)
    print(f"  Raw Git Diff Scale:         {raw_lines:,} lines ({len(raw_diff) / 1024:.1f} KB)")
    print(f"  Unfiltered Raw Tokens:      ~{raw_tokens:,} tokens")
    print(f"  Sentinel Optimized Tokens:  ~{sentinel_tokens:,} tokens")
    print(f"  Token Reduction Ratio:      {reduction_pct:.1f}% context savings")
    print(f"  End-to-End Latency:         {avg_latency_ms:.2f} ms per evaluation")
    print(f"  Peak Working Memory:        {peak_mem_mb:.2f} MB")
    print(f"  Lockfiles Omitted:          {len(result.omitted_noisy_files)} files")
    print("=" * 65)

if __name__ == "__main__":
    run_benchmark()
