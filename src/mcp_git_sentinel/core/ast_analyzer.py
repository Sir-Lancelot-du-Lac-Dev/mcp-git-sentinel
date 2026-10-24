"""AST-level semantic signature extractor for modified code in Git diffs."""

import ast
import importlib.util
import re
from typing import List, Dict, Optional, Any, Tuple


class NativeASTBackend:
    """
    Pure-Python standard library AST backend with regex heuristic fallbacks.
    Guaranteed zero external dependencies.
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
            # Partial diff chunks may not form a complete valid AST module
            pass
        return signatures

    @staticmethod
    def extract_heuristic_signatures(added_lines: List[str]) -> List[str]:
        """Heuristic multi-language signature extraction (TypeScript / JavaScript / Go / Rust / Python)."""
        outlines: List[str] = []
        for line in added_lines:
            line_str = line.strip()

            # Python def / class
            match_py = re.match(r"^(def|class)\s+([A-Za-z0-9_]+)(\(.*?\))?:", line_str)
            if match_py:
                outlines.append(f"[{match_py.group(1).upper()}] {match_py.group(2)}")
                continue

            # TypeScript / JavaScript function, class, export, interface, type
            match_ts = re.match(r"^(export\s+)?(async\s+)?(function|class|interface|type)\s+([A-Za-z0-9_]+)", line_str)
            if match_ts:
                outlines.append(f"[{match_ts.group(3).upper()}] {match_ts.group(4)}")
                continue

            # Go func / type
            match_go = re.match(r"^func\s+(\(.*?\)\s+)?([A-Za-z0-9_]+)\(", line_str)
            if match_go:
                outlines.append(f"[FUNC] {match_go.group(2)}")
                continue

            # Rust fn / struct / impl / enum / trait
            match_rs = re.match(r"^(pub\s+)?(fn|struct|enum|impl|trait)\s+([A-Za-z0-9_]+)", line_str)
            if match_rs:
                outlines.append(f"[{match_rs.group(2).upper()}] {match_rs.group(3)}")
                continue

        return outlines


class TreeSitterBackend:
    """
    Optional Tree-sitter parsing engine for high-fidelity AST outlines.
    Opportunistically activated when 'tree_sitter' is available in the environment.
    """

    _checked_availability: bool = False
    _is_available: bool = False
    _parsers: Dict[str, Any] = {}

    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
    }

    @classmethod
    def is_available(cls) -> bool:
        """Opportunistically detect if tree-sitter bindings are present."""
        if not cls._checked_availability:
            spec = importlib.util.find_spec("tree_sitter")
            cls._is_available = spec is not None
            cls._checked_availability = True
        return cls._is_available

    @classmethod
    def set_availability_for_testing(cls, available: bool) -> None:
        """Hook to inject mock availability during unit tests."""
        cls._checked_availability = True
        cls._is_available = available

    @classmethod
    def _get_parser_for_ext(cls, ext: str) -> Optional[Tuple[Any, str]]:
        """Resolve and initialize a Tree-sitter parser for a given file extension."""
        lang_key = cls.SUPPORTED_LANGUAGES.get(ext)
        if not lang_key:
            return None

        if lang_key in cls._parsers:
            return cls._parsers[lang_key], lang_key

        try:
            import tree_sitter
            # Resolve language grammar module dynamically (e.g. tree_sitter_typescript)
            grammar_mod_name = f"tree_sitter_{lang_key}"
            if not importlib.util.find_spec(grammar_mod_name):
                return None

            grammar_module = importlib.import_module(grammar_mod_name)
            # Support tree-sitter modern language accessor
            lang_func = getattr(grammar_module, f"language_{lang_key}", None) or getattr(grammar_module, "language", None)
            if not lang_func:
                return None

            language = tree_sitter.Language(lang_func())
            parser = tree_sitter.Parser(language)
            cls._parsers[lang_key] = parser
            return parser, lang_key
        except Exception:
            return None

    @classmethod
    def parse_signatures(cls, filepath: str, code_text: str) -> Optional[List[str]]:
        """
        Attempt AST signature extraction via Tree-sitter.
        Returns None if tree-sitter or language grammar is unavailable or fails.
        """
        if not cls.is_available() or not code_text.strip():
            return None

        ext = ""
        for supported_ext in cls.SUPPORTED_LANGUAGES:
            if filepath.endswith(supported_ext):
                ext = supported_ext
                break

        if not ext:
            return None

        parser_info = cls._get_parser_for_ext(ext)
        if not parser_info:
            return None

        parser, lang_name = parser_info
        outlines: List[str] = []

        try:
            tree = parser.parse(bytes(code_text, "utf-8"))
            root = tree.root_node

            def extract_from_node(node):
                ntype = node.type
                # TypeScript / JavaScript definitions
                if ntype in ("class_declaration", "abstract_class_declaration"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[CLASS] {name_node.text.decode('utf-8', errors='ignore')}")
                elif ntype in ("function_declaration", "generator_function_declaration"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[FUNCTION] {name_node.text.decode('utf-8', errors='ignore')}")
                elif ntype in ("method_definition",):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[METHOD] {name_node.text.decode('utf-8', errors='ignore')}")
                elif ntype in ("interface_declaration",):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[INTERFACE] {name_node.text.decode('utf-8', errors='ignore')}")
                elif ntype in ("type_alias_declaration",):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[TYPE] {name_node.text.decode('utf-8', errors='ignore')}")
                # Go definitions
                elif ntype == "function_declaration":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[FUNC] {name_node.text.decode('utf-8', errors='ignore')}")
                elif ntype == "method_declaration":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[METHOD] {name_node.text.decode('utf-8', errors='ignore')}")
                elif ntype == "type_spec":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[TYPE] {name_node.text.decode('utf-8', errors='ignore')}")
                # Rust definitions
                elif ntype == "function_item":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[FN] {name_node.text.decode('utf-8', errors='ignore')}")
                elif ntype in ("struct_item", "enum_item", "trait_item"):
                    name_node = node.child_by_field_name("name")
                    kind = ntype.replace("_item", "").upper()
                    if name_node:
                        outlines.append(f"[{kind}] {name_node.text.decode('utf-8', errors='ignore')}")
                # Python definitions
                elif ntype == "class_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[CLASS] class {name_node.text.decode('utf-8', errors='ignore')}")
                elif ntype == "function_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        outlines.append(f"[FUNC] def {name_node.text.decode('utf-8', errors='ignore')}")

                for child in node.children:
                    extract_from_node(child)

            extract_from_node(root)
            return outlines if outlines else None
        except Exception:
            return None


class ASTAnalyzer:
    """
    Extracts structural code change signatures (classes, functions, methods)
    from unified diffs to provide high-level semantic outlines for AI agents.
    Supports opportunistic Tree-sitter AST parsing with seamless native fallback.
    """

    @staticmethod
    def extract_python_signatures(code_text: str) -> List[Dict[str, str]]:
        """Extract top-level functions, classes, and method signatures via Python AST."""
        return NativeASTBackend.extract_python_signatures(code_text)

    @classmethod
    def is_treesitter_available(cls) -> bool:
        """Check whether Tree-sitter parsing engine is available."""
        return TreeSitterBackend.is_available()

    @classmethod
    def get_active_backend(cls) -> str:
        """Return the active AST parser backend descriptor."""
        return "tree-sitter" if cls.is_treesitter_available() else "native"

    @classmethod
    def extract_semantic_outline_from_diff(cls, filepath: str, diff_content: str) -> List[str]:
        """
        Parses diff additions to identify which functions, classes, or interfaces
        were introduced or modified.
        Opportunistically leverages Tree-sitter when available, falling back to Native AST.
        """
        lines = diff_content.splitlines()
        added_lines = [line[1:] for line in lines if line.startswith("+") and not line.startswith("+++")]
        added_text = "\n".join(added_lines)

        outlines: List[str] = []

        # 1. Opportunistic Tree-sitter AST extraction
        if TreeSitterBackend.is_available() and added_text.strip():
            ts_outlines = TreeSitterBackend.parse_signatures(filepath, added_text)
            if ts_outlines:
                outlines.extend(ts_outlines)

        # 2. Native Fallback if Tree-sitter was unavailable, unsupported, or produced no outline
        if not outlines:
            # Python standard AST parsing
            if filepath.endswith(".py") and added_text.strip():
                ast_sigs = NativeASTBackend.extract_python_signatures(added_text)
                if ast_sigs:
                    for sig in ast_sigs:
                        outlines.append(f"[{sig['type'].upper()}] {sig['signature']}")

            # Multi-language regex heuristic extraction
            if not outlines:
                outlines = NativeASTBackend.extract_heuristic_signatures(added_lines)

        # De-duplicate while preserving appearance order
        unique_outlines: List[str] = []
        seen = set()
        for o in outlines:
            if o not in seen:
                seen.add(o)
                unique_outlines.append(o)

        return unique_outlines[:10]  # Cap at top 10 signatures per file
