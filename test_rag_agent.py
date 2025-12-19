"""
RAG Agent Test Script HW4

Runs test questions with the agentic RAG chatbot and logs detailed results
including reasoning steps, confidence scores, and evaluation metrics.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_agent import RAGAgent, AgentConfig


# Test questions
TEST_QUESTIONS = [
    "What are general rules of clean code?",
    "Understanding Python's runtime environment",
    "What is SonarQube?",
    "Possibility of division by zero",
    "What is Pyflakes?"
]


def run_tests():
    """Run test questions and save detailed results."""
    
    print("\n" + "=" * 70)
    print("  RAG Agent - Detailed Test Script")
    print("=" * 70)
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Questions: {len(TEST_QUESTIONS)}")
    print("=" * 70)
    
    # Initialize agent with verbose config
    config = AgentConfig(
        verbose=True,
        use_reflection=True,
        use_evaluation=True,
        min_confidence_threshold=0.7,
        max_iterations=3
    )
    
    # Use Python knowledge base (Data/python folder with 20+ PDFs)
    agent = RAGAgent(config=config)
    
    # Check if indexed
    if not agent.chatbot.is_indexed:
        print("\n⚠ Knowledge base is empty. Indexing documents first...")
        agent.index_documents()
    
    # Prepare log content
    log_lines = []
    log_lines.append("=" * 70)
    log_lines.append("RAG AGENT - DETAILED TEST RESULTS")
    log_lines.append("=" * 70)
    log_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_lines.append(f"Knowledge Base Size: {agent.chatbot.vector_store.count()} chunks")
    log_lines.append("=" * 70)
    log_lines.append("")
    
    results = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(TEST_QUESTIONS)}] {question}")
        print("=" * 70)
        
        # Get response with detailed output
        response = agent.ask(question, verbose=True)
        
        results.append(response)
        
        # Add to log
        log_lines.append(f"QUESTION {i}:")
        log_lines.append(question)
        log_lines.append("")
        log_lines.append("-" * 50)
        log_lines.append("REASONING STEPS:")
        log_lines.append("-" * 50)
        for step in response.reasoning_steps:
            log_lines.append(f"  • {step}")
        log_lines.append("")
        log_lines.append(f"TOOLS USED: {', '.join(response.tools_used)}")
        log_lines.append("")
        log_lines.append("-" * 50)
        log_lines.append("ANSWER:")
        log_lines.append("-" * 50)
        log_lines.append(response.answer)
        log_lines.append("")
        
        # Sources
        if response.sources:
            source_names = list(set(
                s.get("source", "Unknown") if isinstance(s, dict) else getattr(s, 'source', 'Unknown')
                for s in response.sources[:5]
            ))
            log_lines.append(f"SOURCES: {', '.join(source_names)}")
        else:
            log_lines.append("SOURCES: None")
        log_lines.append("")
        
        # Metrics
        log_lines.append("-" * 50)
        log_lines.append("METRICS:")
        log_lines.append("-" * 50)
        log_lines.append(f"  Confidence: {response.confidence:.2f}")
        log_lines.append(f"  Iterations: {response.iterations}")
        
        if response.evaluation:
            log_lines.append(f"  Grade: {response.evaluation.grade}")
            log_lines.append(f"  Overall Score: {response.evaluation.overall_score:.2f}")
            log_lines.append(f"  Relevance: {response.evaluation.relevance_score:.2f}")
            log_lines.append(f"  Groundedness: {response.evaluation.groundedness_score:.2f}")
            log_lines.append(f"  Clarity: {response.evaluation.clarity_score:.2f}")
            log_lines.append(f"  Completeness: {response.evaluation.completeness_score:.2f}")
            if response.evaluation.feedback:
                log_lines.append(f"  Feedback: {', '.join(response.evaluation.feedback)}")
        
        if response.reflection_summary:
            log_lines.append("")
            log_lines.append("  Reflection Summary:")
            log_lines.append(f"    - Iterations: {response.reflection_summary.get('iterations', 0)}")
            log_lines.append(f"    - Final Confidence: {response.reflection_summary.get('final_confidence', 0):.2f}")
        
        log_lines.append("")
        log_lines.append("=" * 70)
        log_lines.append("")
    
    # Summary
    log_lines.append("")
    log_lines.append("=" * 70)
    log_lines.append("SUMMARY")
    log_lines.append("=" * 70)
    
    avg_confidence = sum(r.confidence for r in results) / len(results)
    avg_score = sum(r.evaluation.overall_score for r in results if r.evaluation) / len(results)
    
    grades = [r.evaluation.grade for r in results if r.evaluation]
    grade_counts = {g: grades.count(g) for g in set(grades)}
    
    log_lines.append(f"Total Questions: {len(results)}")
    log_lines.append(f"Average Confidence: {avg_confidence:.2f}")
    log_lines.append(f"Average Score: {avg_score:.2f}")
    log_lines.append(f"Grade Distribution: {grade_counts}")
    log_lines.append("=" * 70)
    
    # Save log file
    log_path = Path("Rag_chatbot_answer.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    
    print(f"\n{'=' * 70}")
    print(f"✓ Test complete! Results saved to: {log_path.absolute()}")
    print(f"  Average Confidence: {avg_confidence:.2f}")
    print(f"  Average Score: {avg_score:.2f}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_tests()
