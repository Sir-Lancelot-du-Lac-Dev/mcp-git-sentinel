"""Unit tests for AST semantic signature extraction with Tree-sitter & Native backends."""

from unittest.mock import MagicMock, patch
from src.mcp_git_sentinel.core.ast_analyzer import ASTAnalyzer, NativeASTBackend, TreeSitterBackend


def test_python_ast_signatures():
    python_diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -10,3 +10,12 @@ def existing():
+class PaymentProcessor:
+    def process(self, amount, currency):
+        pass
+
+def refund_order(order_id, reason="customer_request"):
+    return True
+"""
    outlines = ASTAnalyzer.extract_semantic_outline_from_diff("app.py", python_diff)
    assert len(outlines) >= 2
    assert any("[CLASS] class PaymentProcessor" in o for o in outlines)
    assert any("refund_order" in o for o in outlines)


def test_multilang_signatures_native():
    ts_diff = """diff --git a/service.ts b/service.ts
--- a/service.ts
+++ b/service.ts
@@ -1,3 +1,5 @@
+export class AuthService {
+export async function verifyToken(jwt: string) {
+interface SessionPayload {
+type AuthResult = boolean;
"""
    # Force native backend
    TreeSitterBackend.set_availability_for_testing(False)
    outlines = ASTAnalyzer.extract_semantic_outline_from_diff("service.ts", ts_diff)
    assert any("[CLASS] AuthService" in o for o in outlines)
    assert any("[FUNCTION] verifyToken" in o for o in outlines)
    assert any("[INTERFACE] SessionPayload" in o for o in outlines)
    assert any("[TYPE] AuthResult" in o for o in outlines)


def test_treesitter_availability_and_active_backend():
    # Should safely return boolean without raising ImportError
    is_avail = TreeSitterBackend.is_available()
    assert isinstance(is_avail, bool)

    active = ASTAnalyzer.get_active_backend()
    assert active in ("tree-sitter", "native")


def test_treesitter_fallback_on_parse_error():
    # When tree-sitter is marked available but parser returns None or errors,
    # it must seamlessly fallback to native parser
    TreeSitterBackend.set_availability_for_testing(True)
    with patch.object(TreeSitterBackend, "parse_signatures", return_value=None):
        py_diff = """diff --git a/fallback.py b/fallback.py
--- a/fallback.py
+++ b/fallback.py
@@ -1,1 +1,2 @@
+def fallback_worker():
+    pass
"""
        outlines = ASTAnalyzer.extract_semantic_outline_from_diff("fallback.py", py_diff)
        assert len(outlines) >= 1
        assert any("fallback_worker" in o for o in outlines)


def test_treesitter_mock_parser_dispatch():
    # Test high-fidelity extraction when TreeSitter returns parsed outlines
    TreeSitterBackend.set_availability_for_testing(True)
    mock_ts_outlines = [
        "[CLASS] OrderAggregateRoot",
        "[METHOD] calculateDiscount",
        "[INTERFACE] IOrderRepository"
    ]
    with patch.object(TreeSitterBackend, "parse_signatures", return_value=mock_ts_outlines):
        diff = """diff --git a/domain.ts b/domain.ts
--- a/domain.ts
+++ b/domain.ts
@@ -0,0 +1,10 @@
+export class OrderAggregateRoot {}
"""
        outlines = ASTAnalyzer.extract_semantic_outline_from_diff("domain.ts", diff)
        assert len(outlines) == 3
        assert outlines[0] == "[CLASS] OrderAggregateRoot"
        assert outlines[1] == "[METHOD] calculateDiscount"
        assert outlines[2] == "[INTERFACE] IOrderRepository"


def test_empty_or_malformed_diff():
    TreeSitterBackend.set_availability_for_testing(False)
    assert ASTAnalyzer.extract_semantic_outline_from_diff("app.py", "") == []
    assert ASTAnalyzer.extract_semantic_outline_from_diff("app.py", "malformed text without diff symbols") == []
