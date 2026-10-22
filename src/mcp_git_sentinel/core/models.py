"""Data models and schemas for Git Sentinel."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class FileDiffSummary:
    """Summary of changes for a single file."""
    path: str
    status: str  # modified, added, deleted, renamed
    additions: int = 0
    deletions: int = 0
    estimated_tokens: int = 0
    is_noisy: bool = False
    diff_content: str = ""


@dataclass
class BranchStatus:
    """Topology and status for the current Git branch."""
    current_branch: str
    upstream_branch: Optional[str] = None
    ahead: int = 0
    behind: int = 0
    staged_count: int = 0
    unstaged_count: int = 0
    untracked_count: int = 0
    recent_commits: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ConflictCheckResult:
    """Pre-flight 3-way merge conflict check result."""
    target_ref: str
    has_conflicts: bool
    conflict_files: List[str] = field(default_factory=list)
    raw_details: str = ""


@dataclass
class SmartDiffResult:
    """Filtered and prioritized semantic diff result."""
    target_ref: str
    total_files_changed: int
    included_files_count: int
    omitted_noisy_files: List[str] = field(default_factory=list)
    total_estimated_tokens: int = 0
    is_truncated: bool = False
    formatted_diff: str = ""
