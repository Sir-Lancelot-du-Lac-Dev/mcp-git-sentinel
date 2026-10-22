"""Low-level Git interaction layer with zero external dependencies."""

import os
import shutil
import subprocess
from typing import List, Dict, Optional, Tuple
from .models import BranchStatus, ConflictCheckResult


class GitExecutionError(Exception):
    """Raised when a Git command fails."""
    pass


class GitInspector:
    """Interacts with the local Git repository via CLI safely."""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = os.path.abspath(repo_path or os.getcwd())
        self._git_bin = shutil.which("git")
        if not self._git_bin:
            raise GitExecutionError("Git executable not found in PATH.")

    def run_git(self, args: List[str]) -> Tuple[int, str, str]:
        """Execute a git command safely in the target repository directory."""
        try:
            proc = subprocess.run(
                [self._git_bin] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            raise GitExecutionError(f"Git command timed out: git {' '.join(args)}")
        except Exception as e:
            raise GitExecutionError(f"Failed to execute git {' '.join(args)}: {str(e)}")

    def is_git_repository(self) -> bool:
        """Check if target path is inside a Git repository."""
        code, stdout, _ = self.run_git(["rev-parse", "--is-inside-work-tree"])
        return code == 0 and stdout.strip() == "true"

    def get_branch_status(self) -> BranchStatus:
        """Inspect the current branch, divergence, and uncommitted file count."""
        if not self.is_git_repository():
            raise GitExecutionError(f"Directory {self.repo_path} is not a valid Git repository.")

        # 1. Current Branch
        _, branch_out, _ = self.run_git(["branch", "--show-current"])
        current_branch = branch_out.strip() or "HEAD (detached)"

        # 2. Upstream Tracking & Divergence
        upstream_branch: Optional[str] = None
        ahead = 0
        behind = 0
        _, upstream_out, _ = self.run_git(["rev-parse", "--abbrev-ref", "@{upstream}"])
        upstream_cand = upstream_out.strip()
        if upstream_cand and not upstream_cand.startswith("@{"):
            upstream_branch = upstream_cand
            # Count ahead/behind
            code, count_out, _ = self.run_git(["rev-list", "--left-right", "--count", f"{upstream_branch}...HEAD"])
            if code == 0:
                parts = count_out.strip().split()
                if len(parts) == 2:
                    behind = int(parts[0])
                    ahead = int(parts[1])

        # 3. Status porcelain to count staged, unstaged, untracked
        staged = 0
        unstaged = 0
        untracked = 0
        code, status_out, _ = self.run_git(["status", "--porcelain"])
        if code == 0:
            for line in status_out.splitlines():
                if len(line) < 2:
                    continue
                index_status = line[0]
                worktree_status = line[1]

                if line.startswith("??"):
                    untracked += 1
                else:
                    if index_status not in (" ", "?"):
                        staged += 1
                    if worktree_status not in (" ", "?"):
                        unstaged += 1

        # 4. Recent commits (last 5)
        recent_commits: List[Dict[str, str]] = []
        code, log_out, _ = self.run_git(["log", "-n", "5", "--pretty=format:%h|%an|%ar|%s"])
        if code == 0 and log_out.strip():
            for line in log_out.splitlines():
                parts = line.split("|", 3)
                if len(parts) == 4:
                    recent_commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "relative_time": parts[2],
                        "subject": parts[3]
                    })

        return BranchStatus(
            current_branch=current_branch,
            upstream_branch=upstream_branch,
            ahead=ahead,
            behind=behind,
            staged_count=staged,
            unstaged_count=unstaged,
            untracked_count=untracked,
            recent_commits=recent_commits
        )

    def get_raw_diff(self, target_ref: Optional[str] = None, staged_only: bool = False) -> str:
        """Fetch raw diff output against target ref or index."""
        args = ["diff"]
        if staged_only:
            args.append("--cached")
        if target_ref:
            args.append(target_ref)
        code, stdout, stderr = self.run_git(args)
        if code != 0:
            raise GitExecutionError(f"git diff failed: {stderr}")
        return stdout

    def detect_merge_conflicts(self, target_ref: str) -> ConflictCheckResult:
        """Simulate a 3-way merge check against target_ref using git merge-tree."""
        if not self.is_git_repository():
            raise GitExecutionError(f"Directory {self.repo_path} is not a valid Git repository.")

        # git merge-tree HEAD <target_ref> (works in modern git without touching working tree)
        code, stdout, stderr = self.run_git(["merge-tree", "HEAD", target_ref])
        
        has_conflicts = False
        conflict_files: List[str] = []

        if code != 0 or "+<<<<<<<" in stdout or "CONFLICT" in stdout:
            has_conflicts = True
            for line in stdout.splitlines():
                if "CONFLICT (" in line or "Auto-merging" in line and has_conflicts:
                    conflict_files.append(line.strip())

        return ConflictCheckResult(
            target_ref=target_ref,
            has_conflicts=has_conflicts,
            conflict_files=conflict_files,
            raw_details=stdout[:2000] if has_conflicts else "No merge conflicts detected."
        )
