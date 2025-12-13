"""
Git Integration for Code Review Agent

Provides functionality to:
1. Review uncommitted changes (git diff)
2. Review a specific commit
3. Review a GitHub Pull Request
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class GitFile:
    """Represents a file from git."""
    path: str
    status: str  # 'M' modified, 'A' added, 'D' deleted
    content: Optional[str] = None
    diff: Optional[str] = None


class GitIntegration:
    """Git operations for code review."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self._validate_git_repo()
    
    def _validate_git_repo(self):
        """Check if path is a git repository."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"{self.repo_path} is not a git repository")
    
    def _run_git(self, *args) -> str:
        """Run a git command and return output."""
        result = subprocess.run(
            ["git"] + list(args),
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git error: {result.stderr}")
        return result.stdout.strip()
    
    def get_changed_files(self, staged_only: bool = False) -> List[GitFile]:
        """Get list of changed files (uncommitted)."""
        if staged_only:
            output = self._run_git("diff", "--cached", "--name-status")
        else:
            output = self._run_git("diff", "--name-status", "HEAD")
        
        files = []
        for line in output.split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 2:
                    status, path = parts[0], parts[1]
                    if path.endswith(".py"):  # Only Python files
                        files.append(GitFile(path=path, status=status))
        
        return files
    
    def get_commit_files(self, commit_hash: str) -> List[GitFile]:
        """Get list of files changed in a specific commit."""
        # Use git show which works for all commits including root
        output = self._run_git("show", "--name-status", "--format=", commit_hash)
        
        files = []
        for line in output.split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 2:
                    status, path = parts[0], parts[1]
                    if path.endswith(".py"):
                        files.append(GitFile(path=path, status=status))
                elif len(parts) == 1 and parts[0].endswith(".py"):
                    # Root commit format may just have filename
                    files.append(GitFile(path=parts[0], status="A"))
        
        return files
    
    def get_file_content(self, path: str, ref: str = "HEAD") -> Optional[str]:
        """Get file content at a specific ref."""
        try:
            return self._run_git("show", f"{ref}:{path}")
        except RuntimeError:
            return None
    
    def get_file_diff(self, path: str, commit_hash: Optional[str] = None) -> str:
        """Get diff for a specific file."""
        if commit_hash:
            return self._run_git("diff", f"{commit_hash}^", commit_hash, "--", path)
        else:
            return self._run_git("diff", "HEAD", "--", path)


class GitHubIntegration:
    """GitHub API integration for PR reviews."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self._github = None
    
    @property
    def github(self):
        """Lazy load GitHub client."""
        if self._github is None:
            if not self.token:
                raise ValueError("GitHub token not configured. Set GITHUB_TOKEN in .env")
            from github import Github
            self._github = Github(self.token)
        return self._github
    
    def get_pr_files(self, repo_name: str, pr_number: int) -> List[GitFile]:
        """Get list of files changed in a PR."""
        repo = self.github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        files = []
        for file in pr.get_files():
            if file.filename.endswith(".py"):
                files.append(GitFile(
                    path=file.filename,
                    status=file.status[0].upper(),  # 'added' -> 'A', 'modified' -> 'M'
                    diff=file.patch if hasattr(file, 'patch') else None
                ))
        
        return files
    
    def get_pr_info(self, repo_name: str, pr_number: int) -> dict:
        """Get PR metadata."""
        repo = self.github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        return {
            "title": pr.title,
            "body": pr.body,
            "author": pr.user.login,
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "state": pr.state,
            "files_count": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "url": pr.html_url
        }
    
    def get_file_content_from_pr(self, repo_name: str, pr_number: int, path: str) -> Optional[str]:
        """Get file content from PR head branch."""
        repo = self.github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        try:
            content = repo.get_contents(path, ref=pr.head.sha)
            return content.decoded_content.decode('utf-8')
        except Exception:
            return None
    
    def post_pr_comment(self, repo_name: str, pr_number: int, comment: str) -> bool:
        """Post a comment on a PR with the review results."""
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(comment)
            return True
        except Exception as e:
            print(f"Failed to post PR comment: {e}")
            return False


def list_changed_files(repo_path: str = ".") -> List[str]:
    """Quick helper to list changed Python files."""
    git = GitIntegration(repo_path)
    files = git.get_changed_files()
    return [f.path for f in files]


def list_commit_files(commit_hash: str, repo_path: str = ".") -> List[str]:
    """Quick helper to list Python files changed in a commit."""
    git = GitIntegration(repo_path)
    files = git.get_commit_files(commit_hash)
    return [f.path for f in files]


def list_pr_files(repo_name: str, pr_number: int) -> List[str]:
    """Quick helper to list Python files changed in a PR."""
    gh = GitHubIntegration()
    files = gh.get_pr_files(repo_name, pr_number)
    return [f.path for f in files]
