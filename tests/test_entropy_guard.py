"""Unit tests for Shannon Entropy calculation and secret detection."""

from src.mcp_git_sentinel.core.entropy_guard import EntropyGuard


def test_shannon_entropy_calculation():
    # Repetitive / simple code tokens have low entropy
    low_entropy = EntropyGuard.calculate_shannon_entropy("aaaaaaaaaaaa")
    assert low_entropy == 0.0

    normal_code = EntropyGuard.calculate_shannon_entropy("def process_user_data(user_id):")
    assert normal_code < 4.0

    # High entropy pseudorandom tokens
    high_entropy = EntropyGuard.calculate_shannon_entropy("dK9#mQ2$zL8@pW4!vN7*xR3^")
    assert high_entropy >= 4.2


def test_secret_pattern_detection():
    sample_diff = """diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,3 +1,4 @@
 import os
+OPENAI_API_KEY = "sk-proj-9876543210abcdef9876543210abcdef98765432"
+GITHUB_TOKEN = "ghp_1234567890abcdef1234567890abcdef1234"
+NORMAL_VAR = "hello_world"
"""
    findings = EntropyGuard.scan_diff_chunk("config.py", sample_diff)
    assert len(findings) >= 2

    patterns = [f.description for f in findings]
    assert any("OpenAI" in p for p in patterns)
    assert any("GitHub" in p for p in patterns)

    # Check masking works
    for f in findings:
        assert "****" in f.masked_value
