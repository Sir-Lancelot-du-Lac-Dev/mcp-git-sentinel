"""Unit tests for diff parsing, token budgeting, and smart diff analysis."""

from src.mcp_git_sentinel.core.diff_analyzer import DiffAnalyzer

SAMPLE_RAW_DIFF = """diff --git a/package-lock.json b/package-lock.json
index 1111111..2222222 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,5 +1,5 @@
 {
-  "version": "1.0.0",
+  "version": "1.0.1",
   "dependencies": {
     "express": "4.19.2"
   }
 }
diff --git a/src/main.py b/src/main.py
index 3333333..4444444 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,3 +10,4 @@ def run():
     print("Starting server")
+    print("Initialized sentinel guard")
"""


def test_parse_unified_diff():
    summaries = DiffAnalyzer.parse_unified_diff(SAMPLE_RAW_DIFF)
    assert len(summaries) == 2

    lock_file = summaries[0]
    assert lock_file.path == "package-lock.json"
    assert lock_file.is_noisy is True
    assert lock_file.additions > 0

    code_file = summaries[1]
    assert code_file.path == "src/main.py"
    assert code_file.is_noisy is False
    assert code_file.additions == 1


def test_smart_diff_noise_filtering():
    result = DiffAnalyzer.analyze_smart_diff(
        raw_diff=SAMPLE_RAW_DIFF,
        target_ref="HEAD",
        max_tokens=4000,
        filter_noise=True
    )
    assert result.total_files_changed == 2
    assert result.included_files_count == 1
    assert "package-lock.json" in result.omitted_noisy_files
    assert "src/main.py" in result.formatted_diff
    # The actual diff block for package-lock.json should be omitted
    assert "### File: `package-lock.json`" not in result.formatted_diff


def test_token_budget_truncation():
    # Set a tiny token limit to force truncation
    result = DiffAnalyzer.analyze_smart_diff(
        raw_diff=SAMPLE_RAW_DIFF,
        target_ref="HEAD",
        max_tokens=30,  # Very small budget
        filter_noise=False
    )
    assert result.is_truncated is True
