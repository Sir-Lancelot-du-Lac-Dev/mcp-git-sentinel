"""Zero-dependency Shannon entropy calculator and secret leak detector for Git changes."""

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SecretFinding:
    """Represents a detected high-entropy token or credential pattern."""
    line_number: int
    matched_pattern: str
    masked_value: str
    entropy: float
    description: str


class EntropyGuard:
    """
    Scans code diffs for accidental API key or secret leakage using Shannon Entropy
    and known credential signatures without any third-party dependencies.
    """

    # Well-known API key & token signatures
    KNOWN_PATTERNS: List[Tuple[str, str, str]] = [
        (r"sk-(?:proj-)?[A-Za-z0-9_-]{32,}", "OpenAI API Key", "sk-proj-****"),
        (r"gh[pousr]_[A-Za-z0-9]{36,}", "GitHub Personal Access Token", "ghp_****"),
        (r"github_pat_[A-Za-z0-9_]{60,}", "GitHub Fine-Grained PAT", "github_pat_****"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID", "AKIA****"),
        (r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}", "Slack Token", "xox-****"),
        (r"hf_[A-Za-z0-9]{34,}", "HuggingFace API Token", "hf_****"),
    ]

    @staticmethod
    def calculate_shannon_entropy(text: str) -> float:
        """
        Calculates Shannon Entropy: H(X) = -sum(P(x) * log2(P(x))).
        Natural English/code is typically 2.0 - 3.5.
        High-entropy secrets, hashes, and keys are typically >= 4.3.
        """
        if not text:
            return 0.0
        length = len(text)
        counts = Counter(text)
        entropy = 0.0
        for count in counts.values():
            p_x = count / length
            entropy -= p_x * math.log2(p_x)
        return round(entropy, 2)

    @classmethod
    def mask_secret(cls, token: str) -> str:
        """Safely mask secret retaining only prefix and suffix hints."""
        if len(token) <= 8:
            return "****"
        return f"{token[:4]}****{token[-4:]}"

    @classmethod
    def scan_diff_chunk(cls, file_path: str, diff_text: str) -> List[SecretFinding]:
        """Scan added diff lines for high-entropy secrets and credential signatures."""
        findings: List[SecretFinding] = []
        lines = diff_text.splitlines()

        for idx, line in enumerate(lines, start=1):
            # Only scan added lines (prefixed with '+', excluding '+++')
            if not line.startswith("+") or line.startswith("+++"):
                continue

            content = line[1:].strip()

            # 1. Pattern matching for modern AI & Cloud credentials
            for pattern, desc, mask_sample in cls.KNOWN_PATTERNS:
                matches = re.findall(pattern, content)
                for match in matches:
                    entropy = cls.calculate_shannon_entropy(match)
                    findings.append(SecretFinding(
                        line_number=idx,
                        matched_pattern=pattern,
                        masked_value=cls.mask_secret(match),
                        entropy=entropy,
                        description=f"Signature Match: {desc}"
                    ))

            # 2. Heuristic high-entropy string tokens (> 20 chars, entropy >= 4.4)
            # Find candidate continuous strings (letters, digits, underscores, dashes)
            candidate_tokens = re.findall(r"[A-Za-z0-9_\-+/]{22,}", content)
            for token in candidate_tokens:
                # Avoid matching common file paths, standard URLs or import statements
                if token.startswith("http") or "/" in token or token.endswith((".py", ".json", ".js", ".html")):
                    continue
                entropy = cls.calculate_shannon_entropy(token)
                if entropy >= 4.4:
                    # Avoid duplicate if already caught by known pattern
                    if not any(f.masked_value == cls.mask_secret(token) for f in findings):
                        findings.append(SecretFinding(
                            line_number=idx,
                            matched_pattern="high-entropy-token",
                            masked_value=cls.mask_secret(token),
                            entropy=entropy,
                            description=f"High-Entropy Secret Alert (H={entropy})"
                        ))

        return findings
