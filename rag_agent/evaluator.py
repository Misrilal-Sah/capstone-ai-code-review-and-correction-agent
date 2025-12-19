"""
RAG Agent Evaluator

Evaluation metrics for RAG responses:
- Relevance: Does the answer match the question intent?
- Groundedness: Is the answer supported by sources?
- Clarity: Is the answer well-structured and clear?
- Completeness: Does the answer address all aspects?
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvaluationResult:
    """Complete evaluation of a RAG response."""
    relevance_score: float  # 0-1
    groundedness_score: float  # 0-1
    clarity_score: float  # 0-1
    completeness_score: float  # 0-1
    overall_score: float  # 0-1
    grade: str  # A, B, C, D, F
    feedback: List[str] = field(default_factory=list)
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "relevance": round(self.relevance_score, 2),
            "groundedness": round(self.groundedness_score, 2),
            "clarity": round(self.clarity_score, 2),
            "completeness": round(self.completeness_score, 2),
            "overall": round(self.overall_score, 2),
            "grade": self.grade,
            "feedback": self.feedback,
            "timestamp": self.timestamp
        }


class RAGEvaluator:
    """
    Evaluator for RAG response quality.
    
    Provides detailed metrics on:
    - Relevance to the question
    - Groundedness in source material
    - Clarity of explanation
    - Completeness of answer
    """
    
    GRADE_THRESHOLDS = {
        "A": 0.9,
        "B": 0.8,
        "C": 0.7,
        "D": 0.6,
        "F": 0.0
    }
    
    def __init__(self, llm_provider=None):
        """
        Initialize evaluator.
        
        Args:
            llm_provider: Optional LLM for deeper evaluation
        """
        self.llm_provider = llm_provider
        self._evaluation_history: List[EvaluationResult] = []
    
    def evaluate(
        self,
        question: str,
        answer: str,
        context: str,
        sources: List[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate a RAG response comprehensively.
        
        Args:
            question: Original question
            answer: Generated answer
            context: Retrieved context
            sources: Source chunks
            
        Returns:
            EvaluationResult with all metrics
        """
        feedback = []
        
        # Evaluate each dimension
        relevance = self._evaluate_relevance(question, answer)
        if relevance < 0.7:
            feedback.append("Consider aligning the answer more closely with the question")
        
        groundedness = self._evaluate_groundedness(answer, context, sources)
        if groundedness < 0.7:
            feedback.append("Ensure claims are supported by the source material")
        
        clarity = self._evaluate_clarity(answer)
        if clarity < 0.7:
            feedback.append("Improve answer structure and clarity")
        
        completeness = self._evaluate_completeness(question, answer, context)
        if completeness < 0.7:
            feedback.append("Address more aspects of the question")
        
        # Calculate overall score (weighted average)
        overall = (
            relevance * 0.30 +
            groundedness * 0.30 +
            clarity * 0.20 +
            completeness * 0.20
        )
        
        # Determine grade
        grade = "F"
        for g, threshold in self.GRADE_THRESHOLDS.items():
            if overall >= threshold:
                grade = g
                break
        
        result = EvaluationResult(
            relevance_score=relevance,
            groundedness_score=groundedness,
            clarity_score=clarity,
            completeness_score=completeness,
            overall_score=overall,
            grade=grade,
            feedback=feedback
        )
        
        self._evaluation_history.append(result)
        return result
    
    def _evaluate_relevance(self, question: str, answer: str) -> float:
        """Evaluate how relevant the answer is to the question."""
        score = 0.5  # Base score
        
        # Extract question keywords
        q_words = set(question.lower().split())
        stopwords = {"what", "is", "the", "a", "an", "how", "why", "when", "where", 
                     "do", "does", "are", "for", "to", "of", "in", "on", "and", "or", "?"}
        q_keywords = q_words - stopwords
        
        if not q_keywords:
            return 0.7
        
        # Check keyword presence in answer
        a_words = set(answer.lower().split())
        overlap = q_keywords & a_words
        keyword_score = len(overlap) / len(q_keywords)
        score += keyword_score * 0.3
        
        # Check for question type alignment
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        if question_lower.startswith("what"):
            if any(w in answer_lower for w in ["is", "are", "refers to", "means"]):
                score += 0.1
        elif question_lower.startswith("how"):
            if any(w in answer_lower for w in ["by", "through", "step", "process"]):
                score += 0.1
        elif question_lower.startswith("why"):
            if any(w in answer_lower for w in ["because", "reason", "since", "due"]):
                score += 0.1
        elif "difference" in question_lower:
            if any(w in answer_lower for w in ["while", "whereas", "unlike", "compared"]):
                score += 0.1
        
        return min(1.0, score)
    
    def _evaluate_groundedness(
        self,
        answer: str,
        context: str,
        sources: List[Dict[str, Any]] = None
    ) -> float:
        """Evaluate if answer is grounded in sources."""
        if not context:
            return 0.3
        
        score = 0.4  # Base score for having context
        
        # Check for content overlap
        context_lower = context.lower()
        answer_lower = answer.lower()
        
        # Extract significant phrases from answer
        answer_words = answer_lower.split()
        context_words = set(context_lower.split())
        
        # Check word overlap
        common_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", 
                       "to", "of", "in", "on", "and", "or", "for", "with", "that", "this"}
        significant_overlap = 0
        for word in answer_words:
            if word not in common_words and word in context_words:
                significant_overlap += 1
        
        if len(answer_words) > 0:
            overlap_ratio = significant_overlap / len(answer_words)
            score += overlap_ratio * 0.4
        
        # Check for hallucination indicators (reduce score)
        hallucination_phrases = [
            "i think", "i believe", "probably", "might be",
            "as far as i know", "in my opinion"
        ]
        for phrase in hallucination_phrases:
            if phrase in answer_lower:
                score -= 0.1
        
        # Bonus for citing sources
        if sources:
            source_names = [s.get("source", "") for s in sources]
            for name in source_names:
                if name.lower() in answer_lower:
                    score += 0.1
                    break
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_clarity(self, answer: str) -> float:
        """Evaluate clarity and structure of the answer."""
        score = 0.5  # Base score
        
        # Check for proper sentence structure
        if answer and answer[0].isupper():
            score += 0.1
        
        if answer.strip().endswith(('.', '!', '?')):
            score += 0.1
        
        # Check for structured content
        sentences = re.split(r'[.!?]', answer)
        valid_sentences = [s for s in sentences if len(s.strip()) > 10]
        
        if len(valid_sentences) >= 2:
            score += 0.1
        
        # Check for lists/bullet points (organized structure)
        if re.search(r'(\d+[\.\):]|\-\s|\•|\*\s)', answer):
            score += 0.1
        
        # Penalize very long sentences (reduce readability)
        words = answer.split()
        if len(sentences) > 0:
            avg_words_per_sentence = len(words) / len(sentences)
            if avg_words_per_sentence > 40:
                score -= 0.1
        
        # Check for coherence markers
        coherence_markers = ["first", "second", "additionally", "moreover", 
                           "however", "therefore", "in conclusion", "finally"]
        for marker in coherence_markers:
            if marker in answer.lower():
                score += 0.05
                break
        
        return min(1.0, score)
    
    def _evaluate_completeness(
        self,
        question: str,
        answer: str,
        context: str
    ) -> float:
        """Evaluate if answer completely addresses the question."""
        score = 0.5  # Base score
        
        # Check answer length relative to question complexity
        q_words = len(question.split())
        a_words = len(answer.split())
        
        if a_words >= q_words * 3:
            score += 0.15
        elif a_words >= q_words * 2:
            score += 0.1
        elif a_words < q_words:
            score -= 0.1
        
        # Check for question with multiple parts
        and_count = question.lower().count(" and ")
        or_count = question.lower().count(" or ")
        parts = 1 + and_count + or_count
        
        # Check if answer addresses multiple parts
        answer_sentences = len(re.split(r'[.!?]', answer))
        if parts > 1 and answer_sentences >= parts:
            score += 0.1
        
        # Check for list expectations
        list_keywords = ["do's", "don'ts", "practices", "steps", "ways", 
                        "methods", "types", "examples", "benefits", "advantages"]
        expects_list = any(kw in question.lower() for kw in list_keywords)
        
        if expects_list:
            # Check if answer has list format
            list_items = len(re.findall(r'(\d+[\.\):]|\-\s|\•|\*\s)', answer))
            if list_items >= 3:
                score += 0.15
            elif list_items >= 1:
                score += 0.1
        
        # Check for comparison questions
        if "difference" in question.lower() or "compare" in question.lower():
            comparison_words = ["while", "whereas", "unlike", "compared to", "on the other hand"]
            if any(w in answer.lower() for w in comparison_words):
                score += 0.1
        
        return min(1.0, score)
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary of all evaluations."""
        if not self._evaluation_history:
            return {"count": 0}
        
        avg_overall = sum(e.overall_score for e in self._evaluation_history) / len(self._evaluation_history)
        
        grade_counts = {}
        for e in self._evaluation_history:
            grade_counts[e.grade] = grade_counts.get(e.grade, 0) + 1
        
        return {
            "count": len(self._evaluation_history),
            "average_overall": round(avg_overall, 2),
            "grade_distribution": grade_counts,
            "average_relevance": round(sum(e.relevance_score for e in self._evaluation_history) / len(self._evaluation_history), 2),
            "average_groundedness": round(sum(e.groundedness_score for e in self._evaluation_history) / len(self._evaluation_history), 2)
        }
    
    def reset(self):
        """Reset evaluation history."""
        self._evaluation_history = []


def evaluate_rag_response(
    question: str,
    answer: str,
    context: str,
    sources: List[Dict[str, Any]] = None
) -> EvaluationResult:
    """
    Convenience function to evaluate a single response.
    
    Args:
        question: Original question
        answer: Generated answer
        context: Retrieved context
        sources: Source chunks
        
    Returns:
        EvaluationResult
    """
    evaluator = RAGEvaluator()
    return evaluator.evaluate(question, answer, context, sources)


if __name__ == "__main__":
    # Test evaluator
    result = evaluate_rag_response(
        question="What are the production Do's for RAG?",
        answer="""The production Do's for RAG include:
1. Use hybrid search combining vector and keyword search
2. Implement proper chunking strategies
3. Add metadata filtering for better relevance
4. Use re-ranking for improved results
5. Monitor and log retrieval quality""",
        context="Production Do's: Use hybrid search, proper chunking, metadata filtering, re-ranking..."
    )
    
    print(f"Overall Score: {result.overall_score:.2f}")
    print(f"Grade: {result.grade}")
    print(f"Relevance: {result.relevance_score:.2f}")
    print(f"Groundedness: {result.groundedness_score:.2f}")
    print(f"Clarity: {result.clarity_score:.2f}")
    print(f"Completeness: {result.completeness_score:.2f}")
    print(f"Feedback: {result.feedback}")
