"""
RAG Agent - Main Entry Point

CLI for the Agentic RAG Chatbot with:
- Interactive chat mode
- Single question asking
- Evaluation mode with test questions
- Knowledge base indexing

Usage:
    python rag_main.py chat                  # Interactive chat
    python rag_main.py ask "question"        # Ask single question
    python rag_main.py evaluate              # Run evaluation tests
    python rag_main.py index                 # Index knowledge base
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_agent import RAGAgent, AgentConfig


# Test questions for evaluation
TEST_QUESTIONS = [
    "What are the production 'Do's' for RAG?",
    "What is the difference between standard retrieval and the ColPali approach?",
    "Why is hybrid search better than vector-only search?",
]


def cmd_chat(args):
    """Run interactive chat mode."""
    config = AgentConfig(
        verbose=True,
        use_reflection=True,
        use_evaluation=True
    )
    
    agent = RAGAgent(
        config=config,
        data_directory=args.data_dir
    )
    
    if not agent.chatbot.is_indexed:
        print("\n⚠ Knowledge base is empty. Indexing documents first...")
        agent.index_documents()
    
    agent.interactive_chat()


def cmd_ask(args):
    """Ask a single question."""
    config = AgentConfig(
        verbose=args.verbose,
        use_reflection=True,
        use_evaluation=True
    )
    
    agent = RAGAgent(
        config=config,
        data_directory=args.data_dir
    )
    
    if not agent.chatbot.is_indexed:
        print("\n⚠ Knowledge base is empty. Indexing documents first...")
        agent.index_documents()
    
    response = agent.ask(args.question)
    
    if not args.verbose:
        print("\n" + "=" * 60)
        print(f"Question: {response.question}")
        print("=" * 60)
    
    print(f"\nAnswer:\n{response.answer}")
    
    # Show sources
    if response.sources:
        source_names = list(set(
            s.get("source", "Unknown") if isinstance(s, dict) else getattr(s, 'source', 'Unknown')
            for s in response.sources[:5]
        ))
        print(f"\nSources: {', '.join(source_names)}")
    
    # Show metrics
    print(f"\nConfidence: {response.confidence:.2f}")
    
    if response.evaluation:
        print(f"Grade: {response.evaluation.grade} (score: {response.evaluation.overall_score:.2f})")
    
    if args.show_reasoning:
        print("\nReasoning Steps:")
        for step in response.reasoning_steps:
            print(f"  - {step}")
        print(f"\nTools Used: {', '.join(response.tools_used)}")
    
    return response


def cmd_evaluate(args):
    """Run evaluation on test questions."""
    print("\n" + "=" * 70)
    print("  RAG Agent - Evaluation Mode")
    print("=" * 70)
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Test Questions: {len(TEST_QUESTIONS)}")
    print("=" * 70)
    
    config = AgentConfig(
        verbose=False,
        use_reflection=True,
        use_evaluation=True
    )
    
    agent = RAGAgent(
        config=config,
        data_directory=args.data_dir
    )
    
    if not agent.chatbot.is_indexed:
        print("\n⚠ Knowledge base is empty. Indexing documents first...")
        agent.index_documents()
    
    results = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(TEST_QUESTIONS)}] {question}")
        print("-" * 70)
        
        response = agent.ask(question, verbose=True)
        
        print(f"\nAnswer:")
        print(f"{response.answer}")
        
        # Sources
        if response.sources:
            source_names = list(set(
                s.get("source", "Unknown") if isinstance(s, dict) else getattr(s, 'source', 'Unknown')
                for s in response.sources[:5]
            ))
            print(f"\nSources: {', '.join(source_names)}")
        
        # Metrics
        print(f"\n--- Metrics ---")
        print(f"Confidence: {response.confidence:.2f}")
        
        if response.evaluation:
            print(f"Grade: {response.evaluation.grade}")
            print(f"  Relevance: {response.evaluation.relevance_score:.2f}")
            print(f"  Groundedness: {response.evaluation.groundedness_score:.2f}")
            print(f"  Clarity: {response.evaluation.clarity_score:.2f}")
            print(f"  Completeness: {response.evaluation.completeness_score:.2f}")
        
        print(f"Iterations: {response.iterations}")
        print(f"Tools Used: {', '.join(response.tools_used)}")
        
        results.append(response.to_dict())
    
    # Summary
    print("\n" + "=" * 70)
    print("  EVALUATION SUMMARY")
    print("=" * 70)
    
    avg_confidence = sum(r["confidence"] for r in results) / len(results)
    avg_score = sum(r["evaluation"]["overall"] for r in results if r["evaluation"]) / len(results)
    
    grades = [r["evaluation"]["grade"] for r in results if r["evaluation"]]
    grade_counts = {g: grades.count(g) for g in set(grades)}
    
    print(f"  Average Confidence: {avg_confidence:.2f}")
    print(f"  Average Score: {avg_score:.2f}")
    print(f"  Grade Distribution: {grade_counts}")
    print(f"  Total Questions: {len(results)}")
    
    # Save results
    output_path = Path(args.output) if args.output else Path("rag_evaluation_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "avg_confidence": avg_confidence,
                "avg_score": avg_score,
                "grade_distribution": grade_counts,
                "total_questions": len(results)
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_path.absolute()}")
    print("=" * 70)
    
    return results


def cmd_index(args):
    """Index knowledge base documents."""
    print("\n" + "=" * 60)
    print("  RAG Agent - Indexing Knowledge Base")
    print("=" * 60)
    
    config = AgentConfig(verbose=True)
    
    agent = RAGAgent(
        config=config,
        data_directory=args.data_dir
    )
    
    count = agent.index_documents(force_reindex=args.force)
    
    print(f"\n✓ Indexed {count} chunks")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="RAG Agent - Agentic Chatbot with Reasoning and Reflection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rag_main.py chat                     # Start interactive chat
  python rag_main.py ask "What is RAG?"       # Ask a question
  python rag_main.py evaluate                 # Run evaluation tests
  python rag_main.py index --force            # Reindex knowledge base
        """
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./Data",
        help="Directory containing knowledge base documents"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("question", type=str, help="Question to ask")
    ask_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    ask_parser.add_argument("--show-reasoning", "-r", action="store_true", help="Show reasoning steps")
    
    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Run evaluation on test questions")
    eval_parser.add_argument("--output", "-o", type=str, help="Output file for results")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index knowledge base documents")
    index_parser.add_argument("--force", "-f", action="store_true", help="Force reindex")
    
    args = parser.parse_args()
    
    # Default to chat if no command
    if not args.command:
        args.command = "chat"
    
    # Execute command
    if args.command == "chat":
        cmd_chat(args)
    elif args.command == "ask":
        cmd_ask(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "index":
        cmd_index(args)


if __name__ == "__main__":
    main()
