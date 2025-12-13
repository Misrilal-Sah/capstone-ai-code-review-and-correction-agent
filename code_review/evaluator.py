"""
Evaluation System for Code Review Agent

Provides metrics for evaluating code review quality:
- Accuracy: Are issues correctly identified?
- Relevance: Are issues meaningful?
- Clarity: Are explanations clear?
- Actionability: Are suggestions practical?

Can compare against reference reviews or use synthetic evaluation.
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvaluationScore:
    """Evaluation scores for a code review."""
    accuracy: float  # 0-5
    relevance: float  # 0-5
    clarity: float  # 0-5
    actionability: float  # 0-5
    overall: float = 0.0  # Computed
    notes: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        self.overall = (self.accuracy + self.relevance + self.clarity + self.actionability) / 4
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "relevance": self.relevance,
            "clarity": self.clarity,
            "actionability": self.actionability,
            "overall": self.overall,
            "notes": self.notes
        }


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    review_path: str
    scores: EvaluationScore
    comparison_method: str  # "synthetic" or "reference"
    true_positives: int = 0
    false_positives: int = 0
    missed_issues: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_path": self.review_path,
            "scores": self.scores.to_dict(),
            "comparison_method": self.comparison_method,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "missed_issues": self.missed_issues
        }


class ReviewEvaluator:
    """
    Evaluates code review quality.
    
    Two modes:
    1. Synthetic: Uses heuristics and LLM to evaluate
    2. Reference: Compares against senior engineer review
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize the evaluator.
        
        Args:
            llm_provider: Optional LLM provider for advanced evaluation
        """
        self.llm = llm_provider
        self.evaluations: List[EvaluationResult] = []
    
    # =========================================================================
    # Main Evaluation Methods
    # =========================================================================
    
    def evaluate_synthetic(
        self,
        review_issues: List[Dict],
        static_issues: List[Dict],
        code: str
    ) -> EvaluationResult:
        """
        Evaluate review using synthetic metrics.
        
        Args:
            review_issues: Issues found by the agent
            static_issues: Ground truth from static analysis
            code: Original code
            
        Returns:
            EvaluationResult with scores
        """
        # Calculate true positives, false positives, missed issues
        static_rules = {issue.get("rule_id") for issue in static_issues}
        review_rules = {issue.get("rule_reference") for issue in review_issues}
        
        true_positives = len(static_rules & review_rules)
        false_positives = len(review_rules - static_rules)
        missed_issues = len(static_rules - review_rules)
        
        # Calculate accuracy (based on TP/FP ratio)
        total_reported = len(review_issues)
        accuracy = 5.0 * (true_positives / max(total_reported, 1)) if total_reported > 0 else 2.5
        
        # Calculate relevance (based on coverage)
        total_issues = len(static_rules)
        relevance = 5.0 * (true_positives / max(total_issues, 1)) if total_issues > 0 else 5.0
        
        # Calculate clarity (heuristic based on suggestion quality)
        clarity = self._evaluate_clarity(review_issues)
        
        # Calculate actionability (heuristic based on fix quality)
        actionability = self._evaluate_actionability(review_issues)
        
        scores = EvaluationScore(
            accuracy=min(accuracy, 5.0),
            relevance=min(relevance, 5.0),
            clarity=clarity,
            actionability=actionability,
            notes={
                "true_positives": f"{true_positives} issues correctly identified",
                "false_positives": f"{false_positives} false alarms",
                "missed_issues": f"{missed_issues} issues missed"
            }
        )
        
        result = EvaluationResult(
            review_path="synthetic",
            scores=scores,
            comparison_method="synthetic",
            true_positives=true_positives,
            false_positives=false_positives,
            missed_issues=missed_issues
        )
        
        self.evaluations.append(result)
        return result
    
    def evaluate_against_reference(
        self,
        review_issues: List[Dict],
        reference_issues: List[Dict]
    ) -> EvaluationResult:
        """
        Evaluate review against a reference (senior engineer) review.
        
        Args:
            review_issues: Issues found by the agent
            reference_issues: Issues from senior engineer review
            
        Returns:
            EvaluationResult with scores
        """
        # Match issues (simplified - by line number and severity)
        def issue_key(issue):
            return (issue.get("line"), issue.get("severity"))
        
        review_keys = {issue_key(i) for i in review_issues}
        reference_keys = {issue_key(i) for i in reference_issues}
        
        matched = len(review_keys & reference_keys)
        agent_only = len(review_keys - reference_keys)
        reference_only = len(reference_keys - review_keys)
        
        # Accuracy based on match rate
        accuracy = 5.0 * (matched / max(len(reference_keys), 1)) if reference_keys else 2.5
        
        # Relevance based on false positive rate
        relevance = 5.0 * (1 - agent_only / max(len(review_keys), 1)) if review_keys else 2.5
        
        # Clarity and actionability need LLM or manual scoring
        clarity = self._evaluate_clarity(review_issues)
        actionability = self._evaluate_actionability(review_issues)
        
        scores = EvaluationScore(
            accuracy=min(accuracy, 5.0),
            relevance=min(relevance, 5.0),
            clarity=clarity,
            actionability=actionability,
            notes={
                "matched_issues": f"{matched} issues matched reference",
                "agent_extras": f"{agent_only} additional issues found by agent",
                "missed_from_reference": f"{reference_only} issues from reference not found"
            }
        )
        
        result = EvaluationResult(
            review_path="reference_comparison",
            scores=scores,
            comparison_method="reference",
            true_positives=matched,
            false_positives=agent_only,
            missed_issues=reference_only
        )
        
        self.evaluations.append(result)
        return result
    
    def evaluate_with_llm(
        self,
        original_code: str,
        review: str,
        suggested_fix: str
    ) -> EvaluationResult:
        """
        Evaluate review using LLM for nuanced scoring.
        
        Args:
            original_code: The original code
            review: The review text
            suggested_fix: The suggested fix
            
        Returns:
            EvaluationResult with LLM-based scores
        """
        if not self.llm:
            raise ValueError("LLM provider required for LLM evaluation")
        
        prompt = f"""Evaluate this code review on a scale of 1-5 for each criterion:

## Original Code:
```python
{original_code}
```

## Code Review:
{review}

## Suggested Fix:
```python
{suggested_fix}
```

## Evaluation Criteria:
1. **Accuracy** (1-5): Are the identified issues real problems?
2. **Relevance** (1-5): Are the issues meaningful and important?
3. **Clarity** (1-5): Are the explanations clear and understandable?
4. **Actionability** (1-5): Are the suggestions practical and implementable?

Provide scores and brief notes for each criterion in JSON format:
{{
    "accuracy": 4,
    "accuracy_note": "All issues are valid",
    "relevance": 5,
    "relevance_note": "Issues are critical",
    "clarity": 3,
    "clarity_note": "Some explanations could be clearer",
    "actionability": 4,
    "actionability_note": "Suggestions are practical"
}}"""

        response = self.llm.generate(
            prompt=prompt,
            complexity="high",
            max_tokens=512
        )
        
        # Parse response
        import re
        json_match = re.search(r'\{[^{}]*\}', response.content, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                scores = EvaluationScore(
                    accuracy=float(data.get("accuracy", 3)),
                    relevance=float(data.get("relevance", 3)),
                    clarity=float(data.get("clarity", 3)),
                    actionability=float(data.get("actionability", 3)),
                    notes={
                        "accuracy": data.get("accuracy_note", ""),
                        "relevance": data.get("relevance_note", ""),
                        "clarity": data.get("clarity_note", ""),
                        "actionability": data.get("actionability_note", "")
                    }
                )
                
                result = EvaluationResult(
                    review_path="llm_evaluation",
                    scores=scores,
                    comparison_method="llm"
                )
                
                self.evaluations.append(result)
                return result
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Fallback to default scores
        return EvaluationResult(
            review_path="llm_evaluation",
            scores=EvaluationScore(3, 3, 3, 3),
            comparison_method="llm_fallback"
        )
    
    # =========================================================================
    # Heuristic Evaluation Methods
    # =========================================================================
    
    def _evaluate_clarity(self, issues: List[Dict]) -> float:
        """Evaluate clarity of issue explanations."""
        if not issues:
            return 3.0
        
        scores = []
        for issue in issues:
            message = issue.get("message", "")
            suggestion = issue.get("suggestion", "")
            
            # Heuristics for clarity
            score = 2.5
            
            # Longer messages are usually clearer
            if len(message) > 50:
                score += 0.5
            if len(message) > 100:
                score += 0.5
            
            # Has specific suggestion
            if suggestion and len(suggestion) > 20:
                score += 1.0
            
            # Has line number reference
            if issue.get("line"):
                score += 0.5
            
            scores.append(min(score, 5.0))
        
        return sum(scores) / len(scores)
    
    def _evaluate_actionability(self, issues: List[Dict]) -> float:
        """Evaluate actionability of suggestions."""
        if not issues:
            return 3.0
        
        scores = []
        for issue in issues:
            suggestion = issue.get("suggestion", "")
            
            score = 2.5
            
            # Has specific suggestion
            if suggestion:
                score += 1.0
            
            # Suggestion has action words
            action_words = ["use", "change", "replace", "add", "remove", "move", "refactor"]
            if any(word in suggestion.lower() for word in action_words):
                score += 0.5
            
            # Has code example in suggestion
            if "```" in suggestion or "`" in suggestion:
                score += 1.0
            
            # Has rule reference
            if issue.get("rule_reference"):
                score += 0.5
            
            scores.append(min(score, 5.0))
        
        return sum(scores) / len(scores)
    
    # =========================================================================
    # Reporting Methods
    # =========================================================================
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all evaluations."""
        if not self.evaluations:
            return {"total_evaluations": 0}
        
        avg_scores = {
            "accuracy": 0,
            "relevance": 0,
            "clarity": 0,
            "actionability": 0,
            "overall": 0
        }
        
        for eval in self.evaluations:
            avg_scores["accuracy"] += eval.scores.accuracy
            avg_scores["relevance"] += eval.scores.relevance
            avg_scores["clarity"] += eval.scores.clarity
            avg_scores["actionability"] += eval.scores.actionability
            avg_scores["overall"] += eval.scores.overall
        
        n = len(self.evaluations)
        for key in avg_scores:
            avg_scores[key] = round(avg_scores[key] / n, 2)
        
        return {
            "total_evaluations": n,
            "average_scores": avg_scores,
            "total_true_positives": sum(e.true_positives for e in self.evaluations),
            "total_false_positives": sum(e.false_positives for e in self.evaluations),
            "total_missed_issues": sum(e.missed_issues for e in self.evaluations)
        }
    
    def generate_report(self, output_path: str = "evaluation_report.md") -> str:
        """Generate markdown evaluation report."""
        summary = self.get_summary()
        
        report = f"""# Code Review Agent Evaluation Report

## Summary

| Metric | Score (1-5) |
|--------|-------------|
| Accuracy | {summary.get('average_scores', {}).get('accuracy', 'N/A'):.2f} |
| Relevance | {summary.get('average_scores', {}).get('relevance', 'N/A'):.2f} |
| Clarity | {summary.get('average_scores', {}).get('clarity', 'N/A'):.2f} |
| Actionability | {summary.get('average_scores', {}).get('actionability', 'N/A'):.2f} |
| **Overall** | **{summary.get('average_scores', {}).get('overall', 'N/A'):.2f}** |

## Issue Detection

- **True Positives:** {summary.get('total_true_positives', 0)}
- **False Positives:** {summary.get('total_false_positives', 0)}
- **Missed Issues:** {summary.get('total_missed_issues', 0)}

## Evaluation Details

"""
        for i, eval in enumerate(self.evaluations, 1):
            report += f"""### Evaluation {i}

- Method: {eval.comparison_method}
- Accuracy: {eval.scores.accuracy:.1f}/5
- Relevance: {eval.scores.relevance:.1f}/5
- Clarity: {eval.scores.clarity:.1f}/5
- Actionability: {eval.scores.actionability:.1f}/5

Notes: {json.dumps(eval.scores.notes, indent=2) if eval.scores.notes else 'None'}

---

"""
        
        Path(output_path).write_text(report, encoding='utf-8')
        return output_path


# =============================================================================
# Scoring Table Generator
# =============================================================================

def generate_scoring_table(evaluation: EvaluationResult) -> str:
    """Generate a markdown scoring table."""
    return f"""
| Criteria | Score (1–5) | Notes |
|----------|-------------|-------|
| Accuracy | {evaluation.scores.accuracy:.1f} | {evaluation.scores.notes.get('accuracy', 'N/A')} |
| Relevance | {evaluation.scores.relevance:.1f} | {evaluation.scores.notes.get('relevance', 'N/A')} |
| Clarity | {evaluation.scores.clarity:.1f} | {evaluation.scores.notes.get('clarity', 'N/A')} |
| Actionability | {evaluation.scores.actionability:.1f} | {evaluation.scores.notes.get('actionability', 'N/A')} |
| **Overall** | **{evaluation.scores.overall:.1f}** | - |
"""


if __name__ == "__main__":
    # Test the evaluator
    evaluator = ReviewEvaluator()
    
    # Sample issues
    review_issues = [
        {"line": 5, "severity": "critical", "message": "SQL injection", "suggestion": "Use parameterized queries", "rule_reference": "SQL_INJECTION"},
        {"line": 3, "severity": "major", "message": "Hardcoded secret", "suggestion": "Use env vars", "rule_reference": "HARDCODED_SECRET"},
    ]
    
    static_issues = [
        {"rule_id": "SQL_INJECTION", "severity": "critical"},
        {"rule_id": "HARDCODED_SECRET", "severity": "major"},
        {"rule_id": "BARE_EXCEPT", "severity": "major"},  # Missed by agent
    ]
    
    result = evaluator.evaluate_synthetic(review_issues, static_issues, "test code")
    
    print("Evaluation Result:")
    print(f"  Accuracy: {result.scores.accuracy:.1f}/5")
    print(f"  Relevance: {result.scores.relevance:.1f}/5")
    print(f"  Clarity: {result.scores.clarity:.1f}/5")
    print(f"  Actionability: {result.scores.actionability:.1f}/5")
    print(f"  Overall: {result.scores.overall:.1f}/5")
    
    print(generate_scoring_table(result))
