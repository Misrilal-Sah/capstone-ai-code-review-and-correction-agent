"""
Code Review Agent

Main agentic loop that orchestrates:
1. Reading and analyzing code
2. Running static analysis
3. Retrieving relevant best practices via RAG
4. Generating code review with LLM
5. Self-reflection and revision
6. Generating corrected code
7. Validating fixes in sandbox
8. Creating output reports
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .llm_provider import TieredLLMProvider, get_llm_provider
from .static_analyzer import StaticAnalyzer, analyze_code
from .tools import CodeReviewTools, CodeReviewResult, ReviewIssue
from .reflection import ReflectionLayer, SimpleReflection


@dataclass
class AgentConfig:
    """Configuration for the Code Review Agent."""
    # LLM settings
    default_complexity: str = "medium"
    use_reflection: bool = True
    max_reflection_iterations: int = 3
    min_confidence_threshold: float = 0.7
    
    # Output settings
    output_dir: str = "./code_review_output"
    generate_inline_comments: bool = True
    generate_corrected_code: bool = True
    generate_markdown_report: bool = True
    
    # Sandbox settings
    validate_fixes: bool = True
    run_black: bool = True
    run_pylint: bool = True
    
    # Safety settings
    auto_apply: bool = False  # Never auto-apply by default


@dataclass
class AuditLogEntry:
    """Audit log entry for a code review."""
    timestamp: str
    input_hash: str
    file_path: str
    language: str
    rules_used: List[str]
    llm_used: str
    issues_found: int
    confidence_scores: List[float]
    review_iterations: int
    static_issues_count: int
    validation_passed: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "input_hash": self.input_hash,
            "file_path": self.file_path,
            "language": self.language,
            "rules_used": self.rules_used,
            "llm_used": self.llm_used,
            "issues_found": self.issues_found,
            "confidence_scores": self.confidence_scores,
            "review_iterations": self.review_iterations,
            "static_issues_count": self.static_issues_count,
            "validation_passed": self.validation_passed
        }


class CodeReviewAgent:
    """
    AI-powered Code Review Agent.
    
    Orchestrates the complete code review pipeline with:
    - Static analysis
    - RAG-based best practice retrieval
    - LLM-powered review generation
    - Self-reflection and revision
    - Sandbox validation
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_provider: Optional[TieredLLMProvider] = None,
        rag_retriever = None  # Optional RAG retriever
    ):
        """
        Initialize the Code Review Agent.
        
        Args:
            config: Agent configuration
            llm_provider: LLM provider (or creates default)
            rag_retriever: Optional RAG retriever for best practices
        """
        self.config = config or AgentConfig()
        self.llm = llm_provider or get_llm_provider()
        self.rag = rag_retriever
        
        # Initialize tools
        self.tools = CodeReviewTools(output_dir=self.config.output_dir)
        self.static_analyzer = StaticAnalyzer()
        self.reflection = ReflectionLayer(self.llm)
        
        # Audit log
        self.audit_log: List[AuditLogEntry] = []
        
        print("✓ CodeReviewAgent initialized")
        print(f"  - Output directory: {self.config.output_dir}")
        print(f"  - Reflection enabled: {self.config.use_reflection}")
        print(f"  - Auto-apply: {self.config.auto_apply} (safety switch)")
    
    # =========================================================================
    # Main Review Methods
    # =========================================================================
    
    def review_file(self, file_path: str, append_report: bool = False) -> CodeReviewResult:
        """
        Review a single Python file.
        
        Args:
            file_path: Path to the Python file
            append_report: If True, append to existing codereview.md
            
        Returns:
            CodeReviewResult with issues, suggestions, and corrected code
        """
        print(f"\n{'='*60}")
        print(f"Reviewing: {file_path}")
        print(f"{'='*60}")
        
        # Step 1: Read the file
        print("\n[1/7] Reading file...")
        code_file = self.tools.file_reader(file_path, include_line_numbers=False)
        code = code_file.content
        
        # Step 2: Run static analysis
        print("[2/7] Running static analysis...")
        static_issues = self.static_analyzer.analyze(code)
        print(f"  Found {len(static_issues)} static analysis issues")
        
        # Step 3: Retrieve relevant best practices (if RAG available)
        print("[3/7] Retrieving best practices...")
        rag_context = self._get_rag_context(code, static_issues)
        
        # Step 4: Generate initial review
        print("[4/7] Generating code review...")
        initial_review, initial_fix = self._generate_review(
            code=code,
            static_issues=static_issues,
            rag_context=rag_context
        )
        
        # Step 5: Self-reflection and revision
        if self.config.use_reflection:
            print("[5/7] Running self-reflection...")
            final_review, final_fix, confidence = self.reflection.refine_review(
                original_code=code,
                initial_review=initial_review,
                suggested_fix=initial_fix,
                static_issues=[i.to_dict() for i in static_issues]
            )
        else:
            final_review = initial_review
            final_fix = initial_fix
            confidence = SimpleReflection.check_review_quality(
                initial_review,
                [i.to_dict() for i in static_issues],
                initial_fix
            ).confidence
        
        # Step 6: Validate fixes in sandbox
        print("[6/7] Validating fixes...")
        validation_result = {"valid": True, "syntax_ok": True}
        if self.config.validate_fixes and final_fix:
            validation_result = self.tools.sandbox_validator(
                final_fix,
                run_black=self.config.run_black,
                run_pylint=self.config.run_pylint
            )
            if validation_result["syntax_ok"]:
                print("  ✓ Suggested fix passed validation")
            else:
                print("  ✗ Suggested fix has issues")
                confidence = max(confidence - 0.2, 0.3)
        
        # Step 7: Generate outputs
        print("[7/7] Generating outputs...")
        
        # Parse review into issues
        issues = self._parse_review_to_issues(final_review, static_issues)
        
        # Create result
        result = CodeReviewResult(
            file_path=file_path,
            issues=issues,
            corrected_code=final_fix if validation_result.get("syntax_ok") else None,
            overall_score=self._calculate_score(issues),
            confidence=confidence
        )
        
        # Generate inline comments
        if self.config.generate_inline_comments:
            result.inline_comments = self.tools.inline_comment_generator(code, issues).split('\n')
        
        # Generate markdown report
        if self.config.generate_markdown_report:
            report_path = self.tools.markdown_writer(result, append=append_report)
            print(f"  ✓ Report saved: {report_path}")
        
        # Save corrected code
        if self.config.generate_corrected_code and result.corrected_code:
            corrected_path = self._save_corrected_code(file_path, result.corrected_code)
            print(f"  ✓ Corrected code saved: {corrected_path}")
        
        # Log audit entry
        self._log_audit(
            file_path=file_path,
            code=code,
            issues=issues,
            static_issues=static_issues,
            confidence=confidence,
            validation_passed=validation_result.get("valid", False)
        )
        
        print(f"\n{'='*60}")
        print(f"Review complete! Confidence: {confidence:.1%}")
        print(f"{'='*60}\n")
        
        return result
    
    def review_code(self, code: str, filename: str = "code.py") -> CodeReviewResult:
        """
        Review code provided as a string.
        
        Args:
            code: Python code as string
            filename: Virtual filename for reporting
            
        Returns:
            CodeReviewResult
        """
        # Save to temp file and review
        temp_path = Path(self.config.output_dir) / f"temp_{filename}"
        temp_path.write_text(code, encoding='utf-8')
        
        try:
            result = self.review_file(str(temp_path))
            result.file_path = filename  # Use virtual filename
            return result
        finally:
            temp_path.unlink(missing_ok=True)
    
    def review_folder(self, folder_path: str) -> List[CodeReviewResult]:
        """Review all Python files in a folder."""
        results = []
        folder = Path(folder_path)
        
        for py_file in folder.rglob("*.py"):
            # Skip __pycache__ and venv
            if "__pycache__" in str(py_file) or "venv" in str(py_file):
                continue
            
            result = self.review_file(str(py_file))
            results.append(result)
        
        return results
    
    # =========================================================================
    # Internal Methods
    # =========================================================================
    
    def _get_rag_context(self, code: str, static_issues: List) -> str:
        """Get relevant best practices from RAG."""
        if not self.rag:
            return self._get_default_context(static_issues)
        
        # Build query from code and issues
        query = f"Python code review best practices for: "
        
        # Add issue categories
        categories = set()
        for issue in static_issues:
            if "security" in issue.rule_id.lower() or "sql" in issue.rule_id.lower():
                categories.add("security")
            elif "docstring" in issue.rule_id.lower():
                categories.add("documentation")
            elif "except" in issue.rule_id.lower():
                categories.add("exception handling")
            elif "long" in issue.rule_id.lower() or "nesting" in issue.rule_id.lower():
                categories.add("code complexity")
        
        query += ", ".join(categories) if categories else "general code quality"
        
        try:
            context = self.rag.retrieve_with_context(query, top_k=5)
            return context
        except Exception as e:
            print(f"  Warning: RAG retrieval failed: {e}")
            return self._get_default_context(static_issues)
    
    def _get_default_context(self, static_issues: List) -> str:
        """Get default best practices context without RAG."""
        rules = []
        
        for issue in static_issues:
            rule_id = issue.rule_id
            if rule_id == "BARE_EXCEPT":
                rules.append("Clean Code: Always catch specific exceptions, never use bare except.")
            elif rule_id == "LONG_FUNCTION":
                rules.append("Clean Code: Functions should be short and do one thing (max ~20 lines).")
            elif rule_id == "MISSING_DOCSTRING":
                rules.append("PEP 257: Public functions and classes should have docstrings.")
            elif rule_id == "SQL_INJECTION":
                rules.append("Security: Use parameterized queries to prevent SQL injection.")
            elif rule_id == "HARDCODED_SECRET":
                rules.append("Security: Never hardcode secrets. Use environment variables.")
            elif rule_id == "MUTABLE_DEFAULT_ARG":
                rules.append("Python Gotcha: Mutable default arguments are shared between calls.")
        
        return "\n".join(rules) if rules else "Follow PEP 8 and Clean Code principles."
    
    def _generate_review(
        self,
        code: str,
        static_issues: List,
        rag_context: str
    ) -> tuple:
        """Generate initial code review."""
        # Use LLM to generate review
        review_response = self.llm.generate_code_review(
            code=code,
            context=rag_context,
            static_issues=[i.to_dict() for i in static_issues],
            complexity=self.config.default_complexity
        )
        
        review = review_response.content
        
        # Generate fix
        fix_response = self.llm.generate_code_fix(
            code=code,
            issues=[i.to_dict() for i in static_issues],
            complexity="high"  # Use best LLM for code generation
        )
        
        # Extract code from response
        fix_code = self._extract_code(fix_response.content)
        
        return review, fix_code
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response."""
        import re
        
        # Try to find code block
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Try generic code block
        code_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Return as-is if no code block found
        return response.strip()
    
    def _parse_review_to_issues(
        self,
        review: str,
        static_issues: List
    ) -> List[ReviewIssue]:
        """Parse review text into structured issues."""
        issues = []
        
        # First, add static analysis issues
        for si in static_issues:
            issues.append(ReviewIssue(
                line=si.line,
                severity=si.severity,
                category=self._issue_to_category(si.rule_id),
                message=si.message,
                suggestion=si.suggestion,
                rule_reference=si.rule_id,
                confidence=0.9  # Static analysis is reliable
            ))
        
        # Parse additional issues from LLM review
        # (simplified - in production would use more sophisticated parsing)
        import re
        
        # Look for patterns like "Line X:" or "[CRITICAL]" etc.
        line_pattern = re.compile(r'line\s*(\d+)', re.IGNORECASE)
        severity_pattern = re.compile(r'\[(critical|major|minor)\]', re.IGNORECASE)
        
        review_lines = review.split('\n')
        for review_line in review_lines:
            # Skip if already covered by static analysis
            line_match = line_pattern.search(review_line)
            if line_match:
                line_no = int(line_match.group(1))
                
                # Check if already reported
                if any(i.line == line_no for i in issues):
                    continue
                
                # Determine severity
                severity_match = severity_pattern.search(review_line)
                severity = severity_match.group(1).lower() if severity_match else "minor"
                
                # Add as new issue
                issues.append(ReviewIssue(
                    line=line_no,
                    severity=severity,
                    category="logic",
                    message=review_line[:100],
                    suggestion="See review for details",
                    confidence=0.7  # LLM-detected, less reliable
                ))
        
        return issues
    
    def _issue_to_category(self, rule_id: str) -> str:
        """Map rule ID to category."""
        rule_id = rule_id.upper()
        
        if any(x in rule_id for x in ["SQL", "SECRET", "SECURITY"]):
            return "security"
        elif any(x in rule_id for x in ["DOCSTRING", "COMMENT", "TODO"]):
            return "documentation"
        elif any(x in rule_id for x in ["LONG", "NESTING", "COMPLEXITY"]):
            return "complexity"
        elif any(x in rule_id for x in ["IMPORT", "GLOBAL"]):
            return "design"
        else:
            return "style"
    
    def _calculate_score(self, issues: List[ReviewIssue]) -> float:
        """Calculate overall code quality score (0-10)."""
        if not issues:
            return 10.0
        
        # Deduct points based on severity
        deductions = {
            "critical": 2.0,
            "major": 1.0,
            "minor": 0.3
        }
        
        total_deduction = sum(deductions.get(i.severity, 0.5) for i in issues)
        score = max(0, 10.0 - total_deduction)
        
        return round(score, 1)
    
    def _save_corrected_code(self, original_path: str, corrected_code: str) -> str:
        """Save corrected code to output directory."""
        original = Path(original_path)
        output_path = Path(self.config.output_dir) / f"corrected_{original.name}"
        output_path.write_text(corrected_code, encoding='utf-8')
        return str(output_path)
    
    def _log_audit(
        self,
        file_path: str,
        code: str,
        issues: List[ReviewIssue],
        static_issues: List,
        confidence: float,
        validation_passed: bool
    ):
        """Log audit entry."""
        import hashlib
        
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            input_hash=hashlib.sha256(code.encode()).hexdigest()[:16],
            file_path=file_path,
            language="python",
            rules_used=list(set(i.rule_reference for i in issues if i.rule_reference)),
            llm_used=self.config.default_complexity,
            issues_found=len(issues),
            confidence_scores=[i.confidence for i in issues],
            review_iterations=len(self.reflection.reflection_history),
            static_issues_count=len(static_issues),
            validation_passed=validation_passed
        )
        
        self.audit_log.append(entry)
        
        # Save audit log
        audit_path = Path(self.config.output_dir) / "audit_log.json"
        with open(audit_path, 'w', encoding='utf-8') as f:
            json.dump([e.to_dict() for e in self.audit_log], f, indent=2)
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get summary of all reviews performed."""
        if not self.audit_log:
            return {"total_reviews": 0}
        
        return {
            "total_reviews": len(self.audit_log),
            "total_issues_found": sum(e.issues_found for e in self.audit_log),
            "average_confidence": sum(sum(e.confidence_scores)/len(e.confidence_scores) if e.confidence_scores else 0 for e in self.audit_log) / len(self.audit_log),
            "validation_pass_rate": sum(1 for e in self.audit_log if e.validation_passed) / len(self.audit_log)
        }


# =============================================================================
# Factory Function
# =============================================================================

def create_agent(
    output_dir: str = "./code_review_output",
    use_reflection: bool = True,
    validate_fixes: bool = True,
    rag_retriever = None
) -> CodeReviewAgent:
    """
    Factory function to create a CodeReviewAgent.
    
    Args:
        output_dir: Directory for output files
        use_reflection: Enable self-reflection
        validate_fixes: Enable sandbox validation
        rag_retriever: Optional RAG retriever
        
    Returns:
        Configured CodeReviewAgent
    """
    config = AgentConfig(
        output_dir=output_dir,
        use_reflection=use_reflection,
        validate_fixes=validate_fixes
    )
    
    return CodeReviewAgent(
        config=config,
        rag_retriever=rag_retriever
    )


if __name__ == "__main__":
    # Test the agent
    agent = create_agent(use_reflection=False)  # Disable reflection for quick test
    
    test_code = '''
def process_user(user_id):
    password = "admin123"
    query = f"SELECT * FROM users WHERE id = {user_id}"
    try:
        result = database.execute(query)
    except:
        pass
    return result
'''
    
    result = agent.review_code(test_code, "test_bad_code.py")
    
    print(f"\nFound {len(result.issues)} issues")
    print(f"Score: {result.overall_score}/10")
    print(f"Confidence: {result.confidence:.1%}")
