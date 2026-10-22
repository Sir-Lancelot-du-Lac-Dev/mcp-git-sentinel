"""Unit tests for AST semantic signature extraction."""

from src.mcp_git_sentinel.core.ast_analyzer import ASTAnalyzer


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
"""
    outlines = ASTAnalyzer.extract_semantic_outline_from_diff("app.py", python_diff)
    assert len(outlines) >= 2
    assert any("[CLASS] class PaymentProcessor" in o for o in outlines)
    assert any("refund_order" in o for o in outlines)


def test_multilang_signatures():
    ts_diff = """diff --git a/service.ts b/service.ts
--- a/service.ts
+++ b/service.ts
@@ -1,3 +1,5 @@
+export class AuthService {
+export async function verifyToken(jwt: string) {
"""
    outlines = ASTAnalyzer.extract_semantic_outline_from_diff("service.ts", ts_diff)
    assert any("[CLASS] AuthService" in o for o in outlines)
    assert any("[FUNCTION] verifyToken" in o for o in outlines)
