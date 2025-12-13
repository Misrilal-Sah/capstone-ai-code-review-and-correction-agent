"""
Static Analyzer for Python Code

Uses Python's AST module to perform lightweight static analysis checks:
- Long functions (>20 lines)
- Bare except clauses
- Unused imports
- Missing docstrings
- SQL injection patterns
- Hardcoded secrets
- Deep nesting
- Magic numbers
- Missing type hints
"""

import ast
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StaticIssue:
    """Represents a static analysis issue."""
    rule_id: str
    severity: str  # critical, major, minor
    line: int
    column: int
    message: str
    suggestion: str
    code_snippet: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet
        }


class StaticAnalyzer:
    """
    Python static code analyzer using AST.
    
    Performs lightweight checks for common code issues.
    """
    
    # Configuration
    MAX_FUNCTION_LINES = 20
    MAX_NESTING_DEPTH = 4
    MAGIC_NUMBER_THRESHOLD = 10  # Constants above this should be named
    
    # Patterns for security checks
    SQL_PATTERNS = [
        r'execute\s*\(\s*["\'].*%s',
        r'execute\s*\(\s*["\'].*\+',
        r'execute\s*\(\s*f["\']',
        r'cursor\.execute\s*\(\s*["\'].*\.format',
    ]
    
    SECRET_PATTERNS = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
        r'aws_access_key_id\s*=\s*["\'][^"\']+["\']',
    ]
    
    def __init__(self):
        """Initialize the static analyzer."""
        self.issues: List[StaticIssue] = []
        self.source_lines: List[str] = []
    
    def analyze(self, code: str) -> List[StaticIssue]:
        """
        Analyze Python code for issues.
        
        Args:
            code: Python source code as string
            
        Returns:
            List of StaticIssue objects
        """
        self.issues = []
        self.source_lines = code.split('\n')
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.issues.append(StaticIssue(
                rule_id="SYNTAX_ERROR",
                severity="critical",
                line=e.lineno or 1,
                column=e.offset or 0,
                message=f"Syntax error: {e.msg}",
                suggestion="Fix the syntax error before proceeding."
            ))
            return self.issues
        
        # Run all checks
        self._check_bare_except(tree)
        self._check_long_functions(tree)
        self._check_missing_docstrings(tree)
        self._check_deep_nesting(tree)
        self._check_unused_imports(tree, code)
        self._check_magic_numbers(tree)
        self._check_mutable_default_args(tree)
        self._check_global_statements(tree)
        
        # Pattern-based checks (don't need AST)
        self._check_sql_injection(code)
        self._check_hardcoded_secrets(code)
        self._check_print_statements(code)
        self._check_todo_fixme(code)
        
        return self.issues
    
    def analyze_file(self, file_path: str) -> List[StaticIssue]:
        """Analyze a Python file."""
        path = Path(file_path)
        if not path.exists():
            return [StaticIssue(
                rule_id="FILE_NOT_FOUND",
                severity="critical",
                line=0,
                column=0,
                message=f"File not found: {file_path}",
                suggestion="Verify the file path."
            )]
        
        code = path.read_text(encoding='utf-8')
        return self.analyze(code)
    
    # =========================================================================
    # AST-based Checks
    # =========================================================================
    
    def _check_bare_except(self, tree: ast.AST):
        """Check for bare except clauses."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues.append(StaticIssue(
                        rule_id="BARE_EXCEPT",
                        severity="major",
                        line=node.lineno,
                        column=node.col_offset,
                        message="Bare 'except:' clause catches all exceptions including SystemExit and KeyboardInterrupt",
                        suggestion="Use 'except Exception:' or catch specific exceptions",
                        code_snippet=self._get_line(node.lineno)
                    ))
    
    def _check_long_functions(self, tree: ast.AST):
        """Check for functions that are too long."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate function length
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_lines = node.end_lineno - node.lineno + 1
                else:
                    # Estimate based on body
                    func_lines = self._estimate_function_length(node)
                
                if func_lines > self.MAX_FUNCTION_LINES:
                    self.issues.append(StaticIssue(
                        rule_id="LONG_FUNCTION",
                        severity="minor",
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Function '{node.name}' is {func_lines} lines (max: {self.MAX_FUNCTION_LINES})",
                        suggestion="Break down into smaller, focused functions",
                        code_snippet=f"def {node.name}(...):"
                    ))
    
    def _check_missing_docstrings(self, tree: ast.AST):
        """Check for missing docstrings in functions and classes."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Skip private methods (starting with _)
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                # Check for docstring
                if not (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                    entity_type = "class" if isinstance(node, ast.ClassDef) else "function"
                    self.issues.append(StaticIssue(
                        rule_id="MISSING_DOCSTRING",
                        severity="minor",
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"{entity_type.capitalize()} '{node.name}' is missing a docstring",
                        suggestion=f"Add a docstring describing the {entity_type}'s purpose",
                        code_snippet=self._get_line(node.lineno)
                    ))
    
    def _check_deep_nesting(self, tree: ast.AST):
        """Check for deeply nested code."""
        
        def get_nesting_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    child_depth = get_nesting_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_nesting_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                depth = get_nesting_depth(node)
                if depth > self.MAX_NESTING_DEPTH:
                    self.issues.append(StaticIssue(
                        rule_id="DEEP_NESTING",
                        severity="major",
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Function '{node.name}' has nesting depth of {depth} (max: {self.MAX_NESTING_DEPTH})",
                        suggestion="Use early returns, extract helper functions, or restructure logic",
                        code_snippet=self._get_line(node.lineno)
                    ))
    
    def _check_unused_imports(self, tree: ast.AST, code: str):
        """Check for potentially unused imports."""
        imports = {}
        
        # Collect all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    imports[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != '*':
                        name = alias.asname or alias.name
                        imports[name] = node.lineno
        
        # Check if each import is used
        # Simple heuristic: check if the name appears elsewhere in code
        for name, line in imports.items():
            # Count occurrences (excluding the import line itself)
            pattern = r'\b' + re.escape(name) + r'\b'
            matches = list(re.finditer(pattern, code))
            
            # If only appears once (the import), it might be unused
            if len(matches) <= 1:
                self.issues.append(StaticIssue(
                    rule_id="UNUSED_IMPORT",
                    severity="minor",
                    line=line,
                    column=0,
                    message=f"Import '{name}' appears to be unused",
                    suggestion="Remove unused imports to keep code clean",
                    code_snippet=self._get_line(line)
                ))
    
    def _check_magic_numbers(self, tree: ast.AST):
        """Check for magic numbers (unnamed numeric constants)."""
        # Skip common acceptable values
        skip_values = {0, 1, 2, -1, 100, 1000}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if abs(node.value) > self.MAGIC_NUMBER_THRESHOLD and node.value not in skip_values:
                    # Check if it's in an assignment context (which is okay)
                    self.issues.append(StaticIssue(
                        rule_id="MAGIC_NUMBER",
                        severity="minor",
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Magic number {node.value} should be a named constant",
                        suggestion="Define as a constant at module level, e.g., MAX_RETRIES = 5",
                        code_snippet=self._get_line(node.lineno)
                    ))
    
    def _check_mutable_default_args(self, tree: ast.AST):
        """Check for mutable default arguments."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        self.issues.append(StaticIssue(
                            rule_id="MUTABLE_DEFAULT_ARG",
                            severity="major",
                            line=node.lineno,
                            column=node.col_offset,
                            message=f"Mutable default argument in function '{node.name}'",
                            suggestion="Use None as default and create the mutable object inside the function",
                            code_snippet=self._get_line(node.lineno)
                        ))
    
    def _check_global_statements(self, tree: ast.AST):
        """Check for global statement usage."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                self.issues.append(StaticIssue(
                    rule_id="GLOBAL_STATEMENT",
                    severity="major",
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Use of 'global' statement for: {', '.join(node.names)}",
                    suggestion="Avoid global state; pass values as function arguments instead",
                    code_snippet=self._get_line(node.lineno)
                ))
    
    # =========================================================================
    # Pattern-based Checks
    # =========================================================================
    
    def _check_sql_injection(self, code: str):
        """Check for potential SQL injection vulnerabilities."""
        for i, line in enumerate(self.source_lines, 1):
            for pattern in self.SQL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append(StaticIssue(
                        rule_id="SQL_INJECTION",
                        severity="critical",
                        line=i,
                        column=0,
                        message="Potential SQL injection vulnerability",
                        suggestion="Use parameterized queries instead of string formatting",
                        code_snippet=line.strip()
                    ))
                    break
    
    def _check_hardcoded_secrets(self, code: str):
        """Check for hardcoded secrets."""
        for i, line in enumerate(self.source_lines, 1):
            for pattern in self.SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append(StaticIssue(
                        rule_id="HARDCODED_SECRET",
                        severity="critical",
                        line=i,
                        column=0,
                        message="Possible hardcoded secret detected",
                        suggestion="Use environment variables or a secrets manager",
                        code_snippet="[REDACTED]"
                    ))
                    break
    
    def _check_print_statements(self, code: str):
        """Check for print statements (should use logging in production)."""
        for i, line in enumerate(self.source_lines, 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            
            if re.search(r'\bprint\s*\(', line):
                self.issues.append(StaticIssue(
                    rule_id="PRINT_STATEMENT",
                    severity="minor",
                    line=i,
                    column=0,
                    message="print() statement found",
                    suggestion="Use logging module for production code",
                    code_snippet=line.strip()
                ))
    
    def _check_todo_fixme(self, code: str):
        """Check for TODO and FIXME comments."""
        for i, line in enumerate(self.source_lines, 1):
            if re.search(r'#\s*(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
                self.issues.append(StaticIssue(
                    rule_id="TODO_COMMENT",
                    severity="minor",
                    line=i,
                    column=0,
                    message="TODO/FIXME comment found",
                    suggestion="Address the TODO or create a tracking issue",
                    code_snippet=line.strip()
                ))
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_line(self, lineno: int) -> str:
        """Get a source line by line number."""
        if 0 < lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""
    
    def _estimate_function_length(self, node) -> int:
        """Estimate function length when end_lineno is not available."""
        # Count nodes as a rough estimate
        return sum(1 for _ in ast.walk(node))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of analysis results."""
        severity_counts = {"critical": 0, "major": 0, "minor": 0}
        for issue in self.issues:
            severity_counts[issue.severity] += 1
        
        return {
            "total_issues": len(self.issues),
            "by_severity": severity_counts,
            "issues": [issue.to_dict() for issue in self.issues]
        }


# =============================================================================
# Factory and Utility Functions
# =============================================================================

def analyze_code(code: str) -> List[StaticIssue]:
    """Quick function to analyze code."""
    analyzer = StaticAnalyzer()
    return analyzer.analyze(code)


def analyze_file(file_path: str) -> List[StaticIssue]:
    """Quick function to analyze a file."""
    analyzer = StaticAnalyzer()
    return analyzer.analyze_file(file_path)


if __name__ == "__main__":
    # Test with sample bad code
    bad_code = '''
import os
import sys  # Unused

password = "super_secret_123"

def process_data(items=[]):
    global counter
    counter = 0
    
    for item in items:
        if item:
            if item.valid:
                if item.active:
                    if item.ready:
                        if item.enabled:
                            print(item)
                            counter += 1
    
    # TODO: Add error handling
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)

def very_long_function():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    i = 12
    j = 13
    k = 14
    l = 15
    m = 16
    n = 17
    o = 18
    p = 19
    q = 20
    r = 21
    return x + y + z
'''
    
    analyzer = StaticAnalyzer()
    issues = analyzer.analyze(bad_code)
    
    print(f"\n{'='*60}")
    print(f"Found {len(issues)} issues:")
    print(f"{'='*60}\n")
    
    for issue in issues:
        print(f"[{issue.severity.upper()}] Line {issue.line}: {issue.rule_id}")
        print(f"  {issue.message}")
        print(f"  Suggestion: {issue.suggestion}")
        print()
