"""Semantic diff analysis, token budgeting, and priority ranking engine."""

import re
from typing import List, Dict, Tuple
from .models import FileDiffSummary, SmartDiffResult
from .noise_filter import NoiseFilter
from .entropy_guard import EntropyGuard, SecretFinding
from .ast_analyzer import ASTAnalyzer


class DiffAnalyzer:
    """Parses, filters, and formats Git diffs for optimal LLM context consumption."""

    # Fast token estimation heuristic for code diffs: ~3.5 chars per token
    CHARS_PER_TOKEN = 3.5

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimate token count from character length."""
        if not text:
            return 0
        return int(len(text) / cls.CHARS_PER_TOKEN) + 1

    @classmethod
    def parse_unified_diff(cls, raw_diff: str) -> List[FileDiffSummary]:
        """Split a unified git diff into individual file summaries."""
        if not raw_diff or not raw_diff.strip():
            return []

        # Split on diff --git
        file_chunks = re.split(r"(?=^diff --git )", raw_diff, flags=re.MULTILINE)
        summaries: List[FileDiffSummary] = []

        for chunk in file_chunks:
            chunk = chunk.strip()
            if not chunk or not chunk.startswith("diff --git"):
                continue

            lines = chunk.splitlines()
            first_line = lines[0]

            # diff --git a/path b/path
            match = re.match(r"^diff --git a/(.*?) b/(.*)$", first_line)
            if match:
                path = match.group(2)
            else:
                path = "unknown"

            # Determine status
            status = "modified"
            if "new file mode" in chunk:
                status = "added"
            elif "deleted file mode" in chunk:
                status = "deleted"
            elif "similarity index" in chunk or "rename from" in chunk:
                status = "renamed"

            # Count additions and deletions
            additions = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
            deletions = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))

            is_noisy = NoiseFilter.is_noisy(path)
            est_tokens = cls.estimate_tokens(chunk)

            summaries.append(FileDiffSummary(
                path=path,
                status=status,
                additions=additions,
                deletions=deletions,
                estimated_tokens=est_tokens,
                is_noisy=is_noisy,
                diff_content=chunk
            ))

        return summaries

    @classmethod
    def analyze_smart_diff(
        cls,
        raw_diff: str,
        target_ref: str = "HEAD",
        max_tokens: int = 4000,
        filter_noise: bool = True,
        scan_secrets: bool = True
    ) -> SmartDiffResult:
        """
        Produce a high-density, filtered diff guaranteed not to overflow max_tokens.
        """
        all_files = cls.parse_unified_diff(raw_diff)
        total_files = len(all_files)

        included_files: List[FileDiffSummary] = []
        omitted_noisy: List[str] = []
        all_secret_findings: List[Tuple[str, SecretFinding]] = []

        for f in all_files:
            # 1. Secret Scanning
            if scan_secrets:
                findings = EntropyGuard.scan_diff_chunk(f.path, f.diff_content)
                for finding in findings:
                    all_secret_findings.append((f.path, finding))

            # 2. Noise Filtering
            if filter_noise and f.is_noisy:
                omitted_noisy.append(f.path)
            else:
                included_files.append(f)

        # Sort remaining files by semantic priority (source code first, then tests, then config)
        included_files.sort(
            key=lambda x: NoiseFilter.get_file_priority(x.path),
            reverse=True
        )

        # Budget token allocations
        budget_remaining = max_tokens
        formatted_chunks: List[str] = []
        is_truncated = False
        accumulated_tokens = 0

        # Header summary
        header = f"# Smart Git Diff Analysis (Target: `{target_ref}`)\n"
        header += f"- **Files Changed:** {total_files} total "
        header += f"({len(included_files)} prioritized, {len(omitted_noisy)} noisy files filtered)\n"
        if omitted_noisy:
            header += f"- **Filtered Noise Files:** `{', '.join(omitted_noisy[:5])}`"
            if len(omitted_noisy) > 5:
                header += f" and {len(omitted_noisy) - 5} more..."
            header += "\n"

        # Security warnings header if secrets detected
        if all_secret_findings:
            header += "\n> 🚨 **SECURITY ALERT: Potential Secret Leakage Detected in Diff!**\n"
            for fpath, item in all_secret_findings:
                header += f"> - In `{fpath}` (Line ~{item.line_number}): **{item.description}** [Masked: `{item.masked_value}`]\n"
            header += "> Please unstage or sanitize these credentials immediately before committing!\n\n"

        header_tokens = cls.estimate_tokens(header)
        budget_remaining -= header_tokens
        accumulated_tokens += header_tokens

        for f in included_files:
            if budget_remaining <= 100:
                is_truncated = True
                break

            # Semantic outline extraction
            outlines = ASTAnalyzer.extract_semantic_outline_from_diff(f.path, f.diff_content)
            outline_str = ""
            if outlines:
                outline_str = "- **Semantic Changes:** " + ", ".join([f"`{o}`" for o in outlines]) + "\n"

            file_header = f"\n### File: `{f.path}` ({f.status}, +{f.additions}/-{f.deletions})\n{outline_str}```diff\n"
            file_footer = "\n```\n"
            overhead = cls.estimate_tokens(file_header + file_footer)

            if f.estimated_tokens <= budget_remaining - overhead:
                # Full diff fits within budget
                formatted_chunks.append(file_header + f.diff_content + file_footer)
                budget_remaining -= (f.estimated_tokens + overhead)
                accumulated_tokens += (f.estimated_tokens + overhead)
            else:
                # File is too large, include partial truncated chunk
                allowed_chars = int((budget_remaining - overhead) * cls.CHARS_PER_TOKEN)
                if allowed_chars > 200:
                    truncated_content = f.diff_content[:allowed_chars] + "\n... [Diff truncated to protect context window] ..."
                    formatted_chunks.append(file_header + truncated_content + file_footer)
                    accumulated_tokens += budget_remaining
                    budget_remaining = 0
                is_truncated = True
                break

        full_output = header + "".join(formatted_chunks)
        if is_truncated:
            full_output += "\n> ⚠️ **Context Notice:** Some diffs were truncated to honor the strict token budget. Use targeted queries for specific files if needed."

        return SmartDiffResult(
            target_ref=target_ref,
            total_files_changed=total_files,
            included_files_count=len(formatted_chunks),
            omitted_noisy_files=omitted_noisy,
            total_estimated_tokens=accumulated_tokens,
            is_truncated=is_truncated,
            formatted_diff=full_output
        )
