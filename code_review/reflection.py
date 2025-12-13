"""
Reflection Layer for Code Review Agent

Implements self-reflection to evaluate and improve code reviews:
- Completeness check: Did we catch all issues?
- Accuracy check: Are issues real problems?
- Security check: Were security concerns addressed?
- Clarity check: Are explanations clear?
- Correctness check: Is the suggested fix correct?

Returns confidence scores and revision suggestions.
"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ReflectionResult:
    """Result of a reflection evaluation."""
    confidence: float  # 0.0 - 1.0
    should_revise: bool
    missed_issues: List[str] = field(default_factory=list)
    false_positives: List[str] = field(default_factory=list)
    fix_issues: List[str] = field(default_factory=list)
    revision_suggestions: List[str] = field(default_factory=list)
    iteration: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": self.confidence,
            "should_revise": self.should_revise,
            "missed_issues": self.missed_issues,
            "false_positives": self.false_positives,
            "fix_issues": self.fix_issues,
            "revision_suggestions": self.revision_suggestions,
            "iteration": self.iteration
        }


class ReflectionLayer:
    """
    Self-reflection layer for evaluating code reviews.
    
    Uses LLM to critically evaluate the review quality and suggest improvements.
    """
    
    # Reflection thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.7
    MAX_ITERATIONS = 3
    
    def __init__(self, llm_provider):
        """
        Initialize the reflection layer.
        
        Args:
            llm_provider: TieredLLMProvider instance
        """
        self.llm = llm_provider
        self.reflection_history: List[ReflectionResult] = []
    
    def evaluate(
        self,
        original_code: str,
        review: str,
        suggested_fix: str,
        static_issues: List[Dict] = None
    ) -> ReflectionResult:
        """
        Evaluate a code review for quality and completeness.
        
        Args:
            original_code: The original code being reviewed
            review: The generated review text
            suggested_fix: The suggested corrected code
            static_issues: Static analysis issues for reference
            
        Returns:
            ReflectionResult with confidence and suggestions
        """
        # Use high-complexity LLM for reflection (GPT-4)
        response = self.llm.generate_reflection(
            original_code=original_code,
            review=review,
            suggested_fix=suggested_fix
        )
        
        # Parse LLM response
        result = self._parse_reflection_response(response.content)
        result.iteration = len(self.reflection_history) + 1
        
        # Cross-check with static analysis
        if static_issues:
            result = self._cross_check_static_issues(result, review, static_issues)
        
        self.reflection_history.append(result)
        return result
    
    def refine_review(
        self,
        original_code: str,
        initial_review: str,
        suggested_fix: str,
        static_issues: List[Dict] = None
    ) -> tuple:
        """
        Iteratively refine a review until confidence threshold is met.
        
        Args:
            original_code: The original code
            initial_review: The initial review text
            suggested_fix: Initial suggested fix
            static_issues: Static analysis issues
            
        Returns:
            Tuple of (final_review, final_fix, final_confidence)
        """
        current_review = initial_review
        current_fix = suggested_fix
        iteration = 0
        
        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            
            # Evaluate current review
            reflection = self.evaluate(
                original_code=original_code,
                review=current_review,
                suggested_fix=current_fix,
                static_issues=static_issues
            )
            
            print(f"  Reflection iteration {iteration}: confidence = {reflection.confidence:.2f}")
            
            # Check if we're confident enough
            if not reflection.should_revise or reflection.confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                print(f"  ✓ Review finalized (confidence: {reflection.confidence:.2f})")
                break
            
            # Revise the review
            current_review, current_fix = self._revise_review(
                original_code=original_code,
                current_review=current_review,
                current_fix=current_fix,
                reflection=reflection
            )
        
        final_confidence = self.reflection_history[-1].confidence if self.reflection_history else 0.5
        return current_review, current_fix, final_confidence
    
    def _parse_reflection_response(self, response: str) -> ReflectionResult:
        """Parse LLM reflection response into structured result."""
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                return ReflectionResult(
                    confidence=float(data.get("confidence", 0.5)),
                    should_revise=bool(data.get("should_revise", False)),
                    missed_issues=list(data.get("missed_issues", [])),
                    false_positives=list(data.get("false_positives", [])),
                    fix_issues=list(data.get("fix_issues", [])),
                    revision_suggestions=list(data.get("revision_suggestions", []))
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        
        # Fallback: estimate from text
        return self._estimate_from_text(response)
    
    def _estimate_from_text(self, response: str) -> ReflectionResult:
        """Estimate reflection result from unstructured text."""
        response_lower = response.lower()
        
        # Estimate confidence from keywords
        confidence = 0.6  # Default
        
        if any(word in response_lower for word in ["excellent", "thorough", "complete", "accurate"]):
            confidence = 0.85
        elif any(word in response_lower for word in ["good", "mostly correct", "minor issues"]):
            confidence = 0.75
        elif any(word in response_lower for word in ["incomplete", "missing", "incorrect", "wrong"]):
            confidence = 0.45
        elif any(word in response_lower for word in ["poor", "many issues", "significant problems"]):
            confidence = 0.3
        
        # Check if revision needed
        should_revise = confidence < self.MIN_CONFIDENCE_THRESHOLD
        
        # Extract suggestions (simple heuristic)
        suggestions = []
        if "should" in response_lower or "could" in response_lower:
            # Extract sentences with suggestions
            sentences = response.split('.')
            for sent in sentences:
                if any(word in sent.lower() for word in ["should", "could", "consider", "recommend"]):
                    suggestions.append(sent.strip())
        
        return ReflectionResult(
            confidence=confidence,
            should_revise=should_revise,
            revision_suggestions=suggestions[:3]  # Top 3
        )
    
    def _cross_check_static_issues(
        self,
        result: ReflectionResult,
        review: str,
        static_issues: List[Dict]
    ) -> ReflectionResult:
        """Cross-check reflection with static analysis."""
        review_lower = review.lower()
        
        # Check if static issues are mentioned in review
        for issue in static_issues:
            rule_id = issue.get("rule_id", "").lower()
            message = issue.get("message", "").lower()
            
            # Check if this issue is addressed in the review
            if rule_id not in review_lower and message[:30] not in review_lower:
                result.missed_issues.append(f"Static analysis issue not addressed: {issue.get('message', 'Unknown')}")
                result.confidence = max(result.confidence - 0.05, 0.3)
                result.should_revise = True
        
        return result
    
    def _revise_review(
        self,
        original_code: str,
        current_review: str,
        current_fix: str,
        reflection: ReflectionResult
    ) -> tuple:
        """Revise the review based on reflection feedback."""
        revision_prompt = f"""You previously reviewed this code:

```python
{original_code}
```

**Your Previous Review:**
{current_review}

**Your Previous Fix:**
```python
{current_fix}
```

**Feedback from Quality Check:**
- Missed Issues: {', '.join(reflection.missed_issues) or 'None'}
- False Positives: {', '.join(reflection.false_positives) or 'None'}
- Fix Problems: {', '.join(reflection.fix_issues) or 'None'}
- Suggestions: {', '.join(reflection.revision_suggestions) or 'None'}

**Instructions:**
1. Address all the feedback above
2. Update your review to be more complete and accurate
3. Fix any issues with your suggested code

Provide the revised review and corrected code."""

        response = self.llm.generate(
            prompt=revision_prompt,
            complexity="high",  # Use GPT-4 for revisions
            max_tokens=2048,
            temperature=0.3
        )
        
        # Extract review and code from response
        revised_review, revised_fix = self._extract_review_and_fix(response.content, current_fix)
        
        return revised_review, revised_fix
    
    def _extract_review_and_fix(self, response: str, fallback_fix: str) -> tuple:
        """Extract review text and code fix from response."""
        # Try to find code block
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        
        if code_match:
            fix = code_match.group(1).strip()
            # Review is everything before the code block
            review = response[:code_match.start()].strip()
        else:
            fix = fallback_fix
            review = response
        
        return review, fix
    
    def get_reflection_summary(self) -> Dict[str, Any]:
        """Get summary of all reflection iterations."""
        if not self.reflection_history:
            return {"iterations": 0, "final_confidence": 0.0}
        
        return {
            "iterations": len(self.reflection_history),
            "final_confidence": self.reflection_history[-1].confidence,
            "confidence_progression": [r.confidence for r in self.reflection_history],
            "total_missed_issues": sum(len(r.missed_issues) for r in self.reflection_history),
            "total_false_positives": sum(len(r.false_positives) for r in self.reflection_history),
        }
    
    def reset(self):
        """Reset reflection history."""
        self.reflection_history = []


# =============================================================================
# Simple Reflection (Without LLM)
# =============================================================================

class SimpleReflection:
    """
    Simple rule-based reflection without LLM.
    
    Useful for quick checks or when LLM is unavailable.
    """
    
    @staticmethod
    def check_review_quality(
        review: str,
        static_issues: List[Dict],
        suggested_fix: str
    ) -> ReflectionResult:
        """
        Perform simple quality checks on a review.
        
        Args:
            review: The review text
            static_issues: Static analysis issues
            suggested_fix: Suggested code fix
            
        Returns:
            ReflectionResult with basic evaluation
        """
        confidence = 1.0
        missed = []
        fix_issues = []
        
        review_lower = review.lower()
        
        # Check 1: Are static issues mentioned?
        for issue in static_issues:
            rule_id = issue.get("rule_id", "").lower()
            if rule_id and rule_id.replace("_", " ") not in review_lower:
                missed.append(f"Didn't mention: {issue.get('message', rule_id)[:50]}")
                confidence -= 0.05
        
        # Check 2: Does the fix have basic syntax?
        if suggested_fix:
            try:
                compile(suggested_fix, "<string>", "exec")
            except SyntaxError as e:
                fix_issues.append(f"Suggested fix has syntax error: {e.msg}")
                confidence -= 0.2
        
        # Check 3: Is the review detailed enough?
        if len(review) < 100:
            missed.append("Review seems too short")
            confidence -= 0.1
        
        # Check 4: Does review have actionable suggestions?
        action_words = ["should", "could", "recommend", "suggest", "change", "fix", "update"]
        if not any(word in review_lower for word in action_words):
            missed.append("Review lacks actionable suggestions")
            confidence -= 0.1
        
        confidence = max(confidence, 0.2)
        should_revise = confidence < 0.7
        
        return ReflectionResult(
            confidence=confidence,
            should_revise=should_revise,
            missed_issues=missed,
            fix_issues=fix_issues
        )


if __name__ == "__main__":
    # Test simple reflection
    test_review = """
    The code has several issues:
    1. Bare except clause on line 5
    2. Hardcoded password on line 2
    
    You should use specific exception handling.
    """
    
    test_issues = [
        {"rule_id": "BARE_EXCEPT", "message": "Bare except clause"},
        {"rule_id": "HARDCODED_SECRET", "message": "Hardcoded password"},
        {"rule_id": "SQL_INJECTION", "message": "SQL injection risk"}
    ]
    
    test_fix = "def safe_function():\n    pass\n"
    
    result = SimpleReflection.check_review_quality(
        test_review, test_issues, test_fix
    )
    
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Should revise: {result.should_revise}")
    print(f"Missed issues: {result.missed_issues}")
