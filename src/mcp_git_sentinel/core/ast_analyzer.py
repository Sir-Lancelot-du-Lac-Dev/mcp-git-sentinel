"""AST-level semantic signature extractor for modified code in Git diffs."""

import ast
import re
from typing import List, Dict, Optional


class ASTAnalyzer:
    """
    Extracts structural code change signatures (classes, functions, methods)
    from unified diffs to provide high-level semantic outlines for AI agents.
    """

    @staticmethod
    def extract_python_signatures(code_text: str) -> List[Dict[str, str]]:
        """Extract top-level functions, classes, and method signatures via Python AST."""
        signatures: List[Dict[str, str]] = []
        try:
            tree = ast.parse(code_text)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    signatures.append({
                        "type": "class",
                        "name": node.name,
                        "signature": f"class {node.name}"
                    })
                elif isinstance(node, ast.FunctionDef) or isinstance(node, getattr(ast, "AsyncFunctionDef", ast.FunctionDef)):
                    args = [arg.arg for arg in node.args.args]
                    sig = f"def {node.name}({', '.join(args)})"
                    signatures.append({
                        "type": "function",
                        "name": node.name,
                        "signature": sig
                    })
        except Exception:
            # Fallback if partial code chunk fails full AST parsing
            pass
        return signatures

    @classmethod
    def extract_semantic_outline_from_diff(cls, filepath: str, diff_content: str) -> List[str]:
        """
        Parses diff additions to identify which functions, classes, or interfaces
        were introduced or modified.
        """
        outlines: List[str] = []
        lines = diff_content.splitlines()

        added_lines = [line[1:] for line in lines if line.startswith("+") and not line.startswith("+++")]
        added_text = "\n".join(added_lines)

        # 1. Python AST parsing
        if filepath.endswith(".py") and added_text.strip():
            ast_sigs = cls.extract_python_signatures(added_text)
            if ast_sigs:
                for sig in ast_sigs:
                    outlines.append(f"[{sig['type'].upper()}] {sig['signature']}")
                return outlines

        # 2. Heuristic multi-language signature extraction (TypeScript / JavaScript / Go / Rust / Python fallback)
        for line in added_lines:
            line_str = line.strip()

            # Python def / class
            match_py = re.match(r"^(def|class)\s+([A-Za-z0-9_]+)(\(.*?\))?:", line_str)
            if match_py:
                outlines.append(f"[{match_py.group(1).upper()}] {match_py.group(2)}")
                continue

            # TypeScript / JavaScript function, class, export, interface
            match_ts = re.match(r"^(export\s+)?(async\s+)?(function|class|interface|type)\s+([A-Za-z0-9_]+)", line_str)
            if match_ts:
                outlines.append(f"[{match_ts.group(3).upper()}] {match_ts.group(4)}")
                continue

            # Go func / type
            match_go = re.match(r"^func\s+(\(.*?\)\s+)?([A-Za-z0-9_]+)\(", line_str)
            if match_go:
                outlines.append(f"[FUNC] {match_go.group(2)}")
                continue

            # Rust fn / struct / impl / enum
            match_rs = re.match(r"^(pub\s+)?(fn|struct|enum|impl)\s+([A-Za-z0-9_]+)", line_str)
            if match_rs:
                outlines.append(f"[{match_rs.group(2).upper()}] {match_rs.group(3)}")
                continue

        # De-duplicate while preserving order
        unique_outlines: List[str] = []
        seen = set()
        for o in outlines:
            if o not in seen:
                seen.add(o)
                unique_outlines.append(o)

        return unique_outlines[:10]  # Cap at top 10 signatures per file
