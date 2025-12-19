"""
RAG Agent Reflection

Self-reflection layer to evaluate and improve RAG responses:
- Check if answer addresses the question
- Verify claims against retrieved context
- Provide confidence scoring
- Suggest improvements
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ReflectionResult:
    """Result of self-reflection on a response."""
    confidence: float  # 0.0 to 1.0
    should_refine: bool
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    grounding_score: float = 0.0  # How well answer is grounded in sources
    relevance_score: float = 0.0  # How relevant answer is to question
    completeness_score: float = 0.0  # How complete the answer is
    iteration: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": round(self.confidence, 2),
            "should_refine": self.should_refine,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "grounding_score": round(self.grounding_score, 2),
            "relevance_score": round(self.relevance_score, 2),
            "completeness_score": round(self.completeness_score, 2),
            "iteration": self.iteration
        }


class RAGReflection:
    """
    Self-reflection layer for RAG responses.
    
    Evaluates response quality and suggests improvements through
    iterative refinement until confidence threshold is met.
    """
    
    MIN_CONFIDENCE_THRESHOLD = 0.7
    MAX_ITERATIONS = 3
    
    def __init__(self, llm_provider=None):
        """
        Initialize reflection layer.
        
        Args:
            llm_provider: Optional LLM for deeper reflection
        """
        self.llm_provider = llm_provider
        self._reflection_history: List[ReflectionResult] = []
    
    def reflect(
        self,
        question: str,
        answer: str,
        context: str,
        sources: List[Dict[str, Any]] = None
    ) -> ReflectionResult:
        """
        Reflect on a RAG response.
        
        Args:
            question: Original question
            answer: Generated answer
            context: Retrieved context used
            sources: List of source chunks
            
        Returns:
            ReflectionResult with scores and suggestions
        """
        issues = []
        suggestions = []
        
        # Check 1: Answer length and substance
        if len(answer) < 20:
            issues.append("Answer is too short")
            suggestions.append("Provide more detailed explanation")
        
        if len(answer) > 2000:
            issues.append("Answer may be too verbose")
            suggestions.append("Consider being more concise")
        
        # Check 2: Relevance - does answer relate to question?
        relevance_score = self._check_relevance(question, answer)
        if relevance_score < 0.5:
            issues.append("Answer may not address the question directly")
            suggestions.append("Focus on answering the specific question asked")
        
        # Check 3: Grounding - is answer supported by context?
        grounding_score = self._check_grounding(answer, context)
        if grounding_score < 0.5:
            issues.append("Answer may not be well-grounded in sources")
            suggestions.append("Ensure claims are supported by retrieved context")
        
        # Check 4: Completeness
        completeness_score = self._check_completeness(question, answer)
        if completeness_score < 0.5:
            issues.append("Answer may be incomplete")
            suggestions.append("Address all aspects of the question")
        
        # Check 5: Hallucination indicators
        hallucination_indicators = [
            "I think", "I believe", "probably", "might be",
            "I'm not sure", "I don't know", "cannot find"
        ]
        for indicator in hallucination_indicators:
            if indicator.lower() in answer.lower():
                issues.append(f"Uncertainty indicator found: '{indicator}'")
                suggestions.append("Provide more definitive answers based on sources")
                break
        
        # Calculate overall confidence
        confidence = (relevance_score * 0.4 + grounding_score * 0.4 + completeness_score * 0.2)
        
        # Adjust confidence based on issues
        confidence -= len(issues) * 0.05
        confidence = max(0.0, min(1.0, confidence))
        
        # Determine if refinement is needed
        should_refine = confidence < self.MIN_CONFIDENCE_THRESHOLD and len(self._reflection_history) < self.MAX_ITERATIONS
        
        result = ReflectionResult(
            confidence=confidence,
            should_refine=should_refine,
            issues=issues,
            suggestions=suggestions,
            grounding_score=grounding_score,
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            iteration=len(self._reflection_history) + 1
        )
        
        self._reflection_history.append(result)
        return result
    
    def _check_relevance(self, question: str, answer: str) -> float:
        """Check how relevant the answer is to the question."""
        # Extract key terms from question
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        # Remove stopwords
        stopwords = {"what", "is", "the", "a", "an", "how", "why", "when", "where", "do", "does", "are", "for", "to", "of", "in", "on", "and", "or"}
        question_keywords = question_words - stopwords
        
        if not question_keywords:
            return 0.7  # Default if no keywords
        
        # Check overlap
        overlap = question_keywords & answer_words
        relevance = len(overlap) / len(question_keywords)
        
        # Boost if question mark terms are addressed
        if "?" in question:
            # Check for question type
            if question.lower().startswith("what"):
                if any(term in answer.lower() for term in ["is", "are", "means", "refers"]):
                    relevance += 0.1
            elif question.lower().startswith("how"):
                if any(term in answer.lower() for term in ["by", "through", "using", "steps"]):
                    relevance += 0.1
            elif question.lower().startswith("why"):
                if any(term in answer.lower() for term in ["because", "reason", "due to", "since"]):
                    relevance += 0.1
        
        return min(1.0, relevance)
    
    def _check_grounding(self, answer: str, context: str) -> float:
        """Check if answer is grounded in the context."""
        if not context:
            return 0.3  # Low score if no context
        
        # Check for key phrases from context appearing in answer
        context_words = set(context.lower().split())
        answer_words = set(answer.lower().split())
        
        # Remove common words
        common = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "on", "and", "or", "for", "with"}
        context_keywords = context_words - common
        
        if not context_keywords:
            return 0.5
        
        overlap = context_keywords & answer_words
        grounding = len(overlap) / min(len(context_keywords), 100)  # Cap the denominator
        
        return min(1.0, grounding * 2)  # Scale up
    
    def _check_completeness(self, question: str, answer: str) -> float:
        """Check if answer completely addresses the question."""
        score = 0.5  # Base score
        
        # Check for proper sentence structure
        if answer.strip() and answer[0].isupper():
            score += 0.1
        
        if answer.strip().endswith(('.', '!', '?')):
            score += 0.1
        
        # Check for substantive content
        sentences = re.split(r'[.!?]', answer)
        if len(sentences) >= 2:
            score += 0.1
        
        # Check answer length relative to question complexity
        question_words = len(question.split())
        answer_words = len(answer.split())
        
        if answer_words >= question_words * 2:
            score += 0.1
        
        # Check for list items if question implies multiple points
        list_indicators = ["do's", "don'ts", "practices", "steps", "ways", "methods", "types"]
        for indicator in list_indicators:
            if indicator in question.lower():
                # Check if answer has list format
                if re.search(r'(\d+[\.\):]|\-|\•|\*)', answer):
                    score += 0.1
                break
        
        return min(1.0, score)
    
    def refine_with_llm(
        self,
        question: str,
        answer: str,
        context: str,
        reflection: ReflectionResult
    ) -> str:
        """
        Use LLM to refine the answer based on reflection.
        
        Args:
            question: Original question
            answer: Current answer
            context: Retrieved context
            reflection: Reflection result with issues
            
        Returns:
            Refined answer
        """
        if not self.llm_provider:
            return answer
        
        issues_str = "\n".join(f"- {issue}" for issue in reflection.issues)
        suggestions_str = "\n".join(f"- {s}" for s in reflection.suggestions)
        
        prompt = f"""Improve this answer based on the feedback provided.

Question: {question}

Current Answer: {answer}

Context (source material):
{context[:1500]}

Issues with current answer:
{issues_str}

Suggestions for improvement:
{suggestions_str}

Provide an improved answer that addresses these issues while staying grounded in the context:"""
        
        try:
            response = self.llm_provider.generate(prompt, max_tokens=500)
            return response.content.strip()
        except Exception as e:
            print(f"  Warning: LLM refinement failed: {e}")
            return answer
    
    def get_reflection_summary(self) -> Dict[str, Any]:
        """Get summary of all reflection iterations."""
        if not self._reflection_history:
            return {"iterations": 0, "final_confidence": 0}
        
        return {
            "iterations": len(self._reflection_history),
            "confidence_progression": [r.confidence for r in self._reflection_history],
            "final_confidence": self._reflection_history[-1].confidence,
            "total_issues": sum(len(r.issues) for r in self._reflection_history),
            "improved": len(self._reflection_history) > 1 and 
                       self._reflection_history[-1].confidence > self._reflection_history[0].confidence
        }
    
    def reset(self):
        """Reset reflection history."""
        self._reflection_history = []


class SimpleReflection:
    """
    Lightweight reflection without LLM.
    Uses rule-based checks only.
    """
    
    @staticmethod
    def quick_check(
        question: str,
        answer: str,
        context: str
    ) -> Tuple[float, List[str]]:
        """
        Quick quality check on an answer.
        
        Returns:
            Tuple of (confidence, list of issues)
        """
        issues = []
        confidence = 0.7
        
        # Basic checks
        if len(answer) < 10:
            issues.append("Answer too short")
            confidence -= 0.2
        
        if not context:
            issues.append("No context available")
            confidence -= 0.1
        
        # Check for "I don't know" type responses
        uncertain_phrases = [
            "i don't know", "cannot find", "no information",
            "not available", "unable to"
        ]
        for phrase in uncertain_phrases:
            if phrase in answer.lower():
                issues.append("Answer indicates uncertainty")
                confidence -= 0.15
                break
        
        return (max(0.0, min(1.0, confidence)), issues)


if __name__ == "__main__":
    # Test reflection
    reflector = RAGReflection()
    
    result = reflector.reflect(
        question="What are the production Do's for RAG?",
        answer="RAG should use good practices. The main things are to do it properly.",
        context="Production Do's for RAG include: 1) Use hybrid search, 2) Implement proper chunking, 3) Add metadata filtering."
    )
    
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Should refine: {result.should_refine}")
    print(f"Issues: {result.issues}")
    print(f"Suggestions: {result.suggestions}")
