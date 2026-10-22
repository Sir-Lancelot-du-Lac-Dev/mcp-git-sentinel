"""Unit tests for GitInspector on temporary repositories."""

import os
import subprocess
import pytest
from src.mcp_git_sentinel.core.git_inspector import GitInspector


@pytest.fixture
def temp_git_repo(tmp_path):
    """Creates a temporary initialized Git repository."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # git init
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo_dir), check=True)

    # Initial commit
    file1 = repo_dir / "README.md"
    file1.write_text("# Test Repo\nInitial content", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(repo_dir), check=True)

    return str(repo_dir)


def test_is_git_repository(temp_git_repo, tmp_path):
    inspector = GitInspector(temp_git_repo)
    assert inspector.is_git_repository() is True

    non_repo = tmp_path / "not_a_repo"
    non_repo.mkdir()
    non_inspector = GitInspector(str(non_repo))
    assert non_inspector.is_git_repository() is False


def test_get_branch_status(temp_git_repo):
    inspector = GitInspector(temp_git_repo)
    status = inspector.get_branch_status()

    assert status.current_branch in ["master", "main"]
    assert len(status.recent_commits) == 1
    assert status.recent_commits[0]["subject"] == "Initial commit"
    assert status.staged_count == 0
    assert status.unstaged_count == 0


def test_uncommitted_changes_status(temp_git_repo):
    inspector = GitInspector(temp_git_repo)

    # Create unstaged change
    readme = os.path.join(temp_git_repo, "README.md")
    with open(readme, "a", encoding="utf-8") as f:
        f.write("\nNew line")

    # Create untracked file
    untracked = os.path.join(temp_git_repo, "new_file.py")
    with open(untracked, "w", encoding="utf-8") as f:
        f.write("print('hello')")

    status = inspector.get_branch_status()
    assert status.unstaged_count == 1
    assert status.untracked_count == 1

    # Check raw diff
    diff_out = inspector.get_raw_diff()
    assert "New line" in diff_out
