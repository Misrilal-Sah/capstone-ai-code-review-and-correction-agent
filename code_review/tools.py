"""
Code Review Tools

Provides tool functions for the code review agent:
- file_reader: Read code files, folders, git diffs
- static_analysis_helper: Run static analysis checks
- code_rewriter: Generate corrected code
- markdown_writer: Create codereview.md report
- inline_comment_generator: Generate git-style inline comments
- sandbox_validator: Validate fixes with black/pylint/py_compile
"""

import os
import re
import subprocess
import tempfile
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .static_analyzer import StaticAnalyzer, StaticIssue


@dataclass
class CodeFile:
    """Represents a code file."""
    path: str
    content: str
    language: str = "python"
    line_count: int = 0
    hash: str = ""
    
    def __post_init__(self):
        self.line_count = len(self.content.split('\n'))
        self.hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class ReviewIssue:
    """Represents a code review issue."""
    line: int
    severity: str  # critical, major, minor
    category: str  # security, style, performance, logic, design
    message: str
    suggestion: str
    rule_reference: Optional[str] = None
    confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "suggestion": self.suggestion,
            "rule_reference": self.rule_reference,
            "confidence": self.confidence
        }


@dataclass
class CodeReviewResult:
    """Complete code review result."""
    file_path: str
    issues: List[ReviewIssue] = field(default_factory=list)
    corrected_code: Optional[str] = None
    inline_comments: List[str] = field(default_factory=list)
    overall_score: float = 0.0
    confidence: float = 0.0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CodeReviewTools:
    """
    Collection of tools for code review operations.
    """
    
    def __init__(self, output_dir: str = "./code_review_output"):
        """
        Initialize code review tools.
        
        Args:
            output_dir: Directory to save generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.static_analyzer = StaticAnalyzer()
    
    # =========================================================================
    # Tool 1: File Reader
    # =========================================================================
    
    def file_reader(
        self,
        path: str,
        include_line_numbers: bool = True
    ) -> CodeFile:
        """
        Read a code file or folder of files.
        
        Args:
            path: Path to file or directory
            include_line_numbers: Whether to include line numbers in output
            
        Returns:
            CodeFile object with content
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        if path.is_file():
            content = path.read_text(encoding='utf-8')
            language = self._detect_language(path.suffix, content)
            
            if include_line_numbers:
                lines = content.split('\n')
                numbered_content = '\n'.join(
                    f"{i+1:4d} | {line}" for i, line in enumerate(lines)
                )
                return CodeFile(
                    path=str(path),
                    content=numbered_content,
                    language=language
                )
            
            return CodeFile(
                path=str(path),
                content=content,
                language=language
            )
        
        elif path.is_dir():
            # Read all Python files in directory
            all_content = []
            for py_file in path.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    file_content = py_file.read_text(encoding='utf-8')
                    all_content.append(f"# File: {py_file}\n{file_content}")
            
            combined = "\n\n" + "="*60 + "\n\n".join(all_content)
            return CodeFile(
                path=str(path),
                content=combined,
                language="python"
            )
        
        raise ValueError(f"Invalid path type: {path}")
    
    def read_git_diff(self, repo_path: str = ".") -> str:
        """Read git diff from repository."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout or "No staged changes."
            return f"Git error: {result.stderr}"
        except Exception as e:
            return f"Failed to read git diff: {e}"
    
    # =========================================================================
    # Tool 2: Static Analysis Helper
    # =========================================================================
    
    def static_analysis_helper(
        self,
        code: str,
        language: str = "python"
    ) -> List[Dict[str, Any]]:
        """
        Run static analysis on code.
        
        Args:
            code: Source code string
            language: Programming language
            
        Returns:
            List of issues as dictionaries
        """
        if language != "python":
            return [{"message": f"Static analysis not yet supported for {language}"}]
        
        issues = self.static_analyzer.analyze(code)
        return [issue.to_dict() for issue in issues]
    
    def get_static_analysis_summary(self, code: str) -> Dict[str, Any]:
        """Get a summary of static analysis results."""
        self.static_analyzer.analyze(code)
        return self.static_analyzer.get_summary()
    
    # =========================================================================
    # Tool 3: Markdown Writer
    # =========================================================================
    
    def markdown_writer(
        self,
        review_result: CodeReviewResult,
        output_path: Optional[str] = None,
        append: bool = False
    ) -> str:
        """
        Create a codereview.md report.
        
        Args:
            review_result: CodeReviewResult object
            output_path: Optional custom output path
            append: If True, append to existing file instead of overwriting
            
        Returns:
            Path to the generated markdown file
        """
        output_path = output_path or str(self.output_dir / "codereview.md")
        
        md_content = self._generate_markdown_report(review_result)
        
        if append and Path(output_path).exists():
            # Append with separator
            existing = Path(output_path).read_text(encoding='utf-8')
            md_content = existing + "\n\n---\n\n" + "=" * 60 + "\n\n" + md_content
        
        Path(output_path).write_text(md_content, encoding='utf-8')
        return output_path
    
    def clear_output(self):
        """Clear all corrected files and codereview.md from output directory."""
        # Remove codereview.md
        codereview_path = self.output_dir / "codereview.md"
        if codereview_path.exists():
            codereview_path.unlink()
        
        # Remove all corrected_*.py files
        for corrected_file in self.output_dir.glob("corrected_*.py"):
            corrected_file.unlink()
        
        # Remove audit log
        audit_path = self.output_dir / "audit_log.json"
        if audit_path.exists():
            audit_path.unlink()
    
    def _generate_markdown_report(self, result: CodeReviewResult) -> str:
        """Generate markdown report content."""
        
        # Group issues by severity
        critical = [i for i in result.issues if i.severity == "critical"]
        major = [i for i in result.issues if i.severity == "major"]
        minor = [i for i in result.issues if i.severity == "minor"]
        
        md = f"""# Code Review Report

**File:** `{result.file_path}`  
**Generated:** {result.timestamp}  
**Overall Confidence:** {result.confidence:.1%}  

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {len(critical)} |
| 🟠 Major | {len(major)} |
| 🟡 Minor | {len(minor)} |
| **Total** | **{len(result.issues)}** |

---

"""
        if critical:
            md += "## 🔴 Critical Issues\n\n"
            for issue in critical:
                md += self._format_issue_md(issue)
        
        if major:
            md += "## 🟠 Major Issues\n\n"
            for issue in major:
                md += self._format_issue_md(issue)
        
        if minor:
            md += "## 🟡 Minor Issues\n\n"
            for issue in minor:
                md += self._format_issue_md(issue)
        
        if result.corrected_code:
            md += f"""---

## Suggested Corrected Code

```python
{result.corrected_code}
```

"""
        
        md += """---

## Review Confidence Scores

Each issue has a confidence score (0.0-1.0) indicating how certain the reviewer is.

| Confidence | Meaning |
|------------|---------|
| 0.9 - 1.0 | Very confident, likely a real issue |
| 0.7 - 0.9 | Confident, should be reviewed |
| 0.5 - 0.7 | Moderate, may be false positive |
| < 0.5 | Low confidence, verify manually |

---

*Generated by AI Code Review Agent*
"""
        
        return md
    
    def _format_issue_md(self, issue: ReviewIssue) -> str:
        """Format a single issue as markdown."""
        confidence_emoji = "🟢" if issue.confidence > 0.8 else "🟡" if issue.confidence > 0.5 else "🔴"
        
        return f"""### Line {issue.line}: {issue.message}

- **Category:** {issue.category}
- **Confidence:** {confidence_emoji} {issue.confidence:.1%}
- **Suggestion:** {issue.suggestion}
{f'- **Rule:** {issue.rule_reference}' if issue.rule_reference else ''}

---

"""
    
    # =========================================================================
    # Tool 4: Inline Comment Generator
    # =========================================================================
    
    def inline_comment_generator(
        self,
        code: str,
        issues: List[ReviewIssue]
    ) -> str:
        """
        Generate git-style inline comments.
        
        Args:
            code: Original code
            issues: List of issues
            
        Returns:
            Code with inline comments
        """
        lines = code.split('\n')
        
        # Group issues by line
        issues_by_line = {}
        for issue in issues:
            if issue.line not in issues_by_line:
                issues_by_line[issue.line] = []
            issues_by_line[issue.line].append(issue)
        
        # Insert comments
        result_lines = []
        for i, line in enumerate(lines, 1):
            result_lines.append(line)
            
            if i in issues_by_line:
                for issue in issues_by_line[i]:
                    severity_marker = {"critical": "!!!", "major": "!!", "minor": "!"}
                    marker = severity_marker.get(issue.severity, "!")
                    comment = f"# {marker} [{issue.severity.upper()}] {issue.message}"
                    result_lines.append(comment)
                    result_lines.append(f"#     Suggestion: {issue.suggestion}")
        
        return '\n'.join(result_lines)
    
    def generate_github_review_comments(
        self,
        issues: List[ReviewIssue],
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Generate GitHub-style review comments."""
        comments = []
        for issue in issues:
            comments.append({
                "path": file_path,
                "line": issue.line,
                "body": f"**[{issue.severity.upper()}]** {issue.message}\n\n"
                       f"**Suggestion:** {issue.suggestion}\n\n"
                       f"*Confidence: {issue.confidence:.0%}*"
            })
        return comments
    
    # =========================================================================
    # Tool 5: Sandbox Validator
    # =========================================================================
    
    def sandbox_validator(
        self,
        code: str,
        run_black: bool = True,
        run_pylint: bool = True,
        run_syntax_check: bool = True
    ) -> Dict[str, Any]:
        """
        Validate code in a sandbox environment.
        
        Args:
            code: Python code to validate
            run_black: Run black formatter check
            run_pylint: Run pylint check
            run_syntax_check: Run syntax check
            
        Returns:
            Validation results
        """
        results = {
            "valid": True,
            "syntax_ok": True,
            "black_ok": True,
            "pylint_score": None,
            "errors": [],
            "warnings": []
        }
        
        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Syntax check
            if run_syntax_check:
                syntax_result = self._check_syntax(code)
                results["syntax_ok"] = syntax_result["ok"]
                if not syntax_result["ok"]:
                    results["valid"] = False
                    results["errors"].append(syntax_result["error"])
            
            # Black check
            if run_black:
                black_result = self._run_black_check(temp_path)
                results["black_ok"] = black_result["ok"]
                if not black_result["ok"]:
                    results["warnings"].append("Code does not conform to Black formatting")
            
            # Pylint check
            if run_pylint:
                pylint_result = self._run_pylint(temp_path)
                results["pylint_score"] = pylint_result.get("score")
                results["warnings"].extend(pylint_result.get("issues", []))
        
        finally:
            # Clean up temp file
            os.unlink(temp_path)
        
        return results
    
    def _check_syntax(self, code: str) -> Dict[str, Any]:
        """Check Python syntax."""
        try:
            compile(code, "<string>", "exec")
            return {"ok": True, "error": None}
        except SyntaxError as e:
            return {"ok": False, "error": f"Line {e.lineno}: {e.msg}"}
    
    def _run_black_check(self, file_path: str) -> Dict[str, Any]:
        """Run black --check on file."""
        try:
            result = subprocess.run(
                ["python", "-m", "black", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"ok": result.returncode == 0}
        except Exception as e:
            return {"ok": True, "error": str(e)}  # Don't fail if black not installed
    
    def _run_pylint(self, file_path: str) -> Dict[str, Any]:
        """Run pylint on file."""
        try:
            result = subprocess.run(
                ["python", "-m", "pylint", "--score=y", "--output-format=text", file_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Extract score
            score_match = re.search(r'rated at ([\d.]+)/10', result.stdout)
            score = float(score_match.group(1)) if score_match else None
            
            # Extract issues (simplified)
            issues = []
            for line in result.stdout.split('\n'):
                if re.match(r'^\S+:\d+:', line):
                    issues.append(line)
            
            return {"score": score, "issues": issues[:5]}  # Top 5 issues
        
        except Exception as e:
            return {"score": None, "issues": [], "error": str(e)}
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _detect_language(self, extension: str, content: str) -> str:
        """Detect programming language from extension and content."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".php": "php",
            ".java": "java",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
        }
        
        lang = extension_map.get(extension.lower(), "unknown")
        
        # Shebang detection
        if lang == "unknown" and content.startswith("#!"):
            first_line = content.split('\n')[0]
            if "python" in first_line:
                lang = "python"
            elif "node" in first_line:
                lang = "javascript"
            elif "php" in first_line:
                lang = "php"
        
        return lang


# =============================================================================
# Factory Function
# =============================================================================

def get_tools(output_dir: str = "./code_review_output") -> CodeReviewTools:
    """Factory function to create CodeReviewTools."""
    return CodeReviewTools(output_dir=output_dir)


if __name__ == "__main__":
    # Test the tools
    tools = get_tools()
    
    # Test file reader
    test_code = '''
def bad_function():
    password = "secret123"
    query = f"SELECT * FROM users WHERE id = {user_id}"
    try:
        execute(query)
    except:
        pass
'''
    
    # Test static analysis
    print("Testing static analysis...")
    issues = tools.static_analysis_helper(test_code)
    print(f"Found {len(issues)} issues")
    
    # Test sandbox validator
    print("\nTesting sandbox validator...")
    valid_code = "def hello():\n    print('Hello')\n"
    result = tools.sandbox_validator(valid_code)
    print(f"Syntax OK: {result['syntax_ok']}")
    print(f"Black OK: {result['black_ok']}")
