"""
RAG Agent

Main agentic loop that orchestrates:
1. Receiving user questions
2. Reasoning about what tools to use
3. Executing tool calls (knowledge_search, clarify, summarize)
4. Generating responses with LLM
5. Self-reflecting on response quality
6. Iteratively refining until confidence threshold met
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_chatbot.chatbot import RAGChatbot
from rag_chatbot.retriever import Retriever, RetrievedChunk
from rag_chatbot.embedder import Embedder
from rag_chatbot.vector_store import VectorStore

from .tools import RAGTools, ToolResult
from .reflection import RAGReflection, ReflectionResult
from .evaluator import RAGEvaluator, EvaluationResult


@dataclass
class AgentResponse:
    """Complete response from the RAG Agent."""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    evaluation: Optional[EvaluationResult] = None
    reasoning_steps: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    reflection_summary: Optional[Dict[str, Any]] = None
    iterations: int = 1
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "sources": self.sources,
            "confidence": round(self.confidence, 2),
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "reasoning_steps": self.reasoning_steps,
            "tools_used": self.tools_used,
            "reflection_summary": self.reflection_summary,
            "iterations": self.iterations,
            "timestamp": self.timestamp
        }


@dataclass 
class AgentConfig:
    """Configuration for the RAG Agent."""
    min_confidence_threshold: float = 0.7
    max_iterations: int = 3
    use_reflection: bool = True
    use_evaluation: bool = True
    verbose: bool = True
    top_k_retrieval: int = 5


class RAGAgent:
    """
    Agentic RAG Chatbot.
    
    An autonomous agent that:
    - Reasons about how to answer questions
    - Uses tools to search knowledge base
    - Self-reflects on response quality
    - Iteratively improves answers
    - Provides evaluation metrics
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        data_directory: str = "./Data",  # Searches recursively including Data/python/
        persist_directory: str = "./chroma_db",
        collection_name: str = "python_knowledge",  # Collection with Python docs
        llm_provider=None
    ):
        """
        Initialize the RAG Agent.
        
        Args:
            config: Agent configuration
            data_directory: Directory with knowledge base documents
            persist_directory: ChromaDB persistence directory
            collection_name: Name of the vector collection
            llm_provider: Optional external LLM provider
        """
        self.config = config or AgentConfig()
        
        print("=" * 60)
        print("Initializing RAG Agent")
        print("=" * 60)
        
        # Initialize base RAG chatbot (reuse existing infrastructure)
        print("\n[1/4] Loading RAG pipeline...")
        self.chatbot = RAGChatbot(
            data_directory=data_directory,
            persist_directory=persist_directory,
            collection_name=collection_name,
            use_light_llm=True
        )
        
        # Set up LLM provider
        self.llm_provider = llm_provider
        if not self.llm_provider:
            self._load_llm_provider()
        
        # Initialize tools
        print("\n[2/4] Setting up tools...")
        self.tools = RAGTools(
            retriever=self.chatbot.retriever,
            llm_provider=self.llm_provider
        )
        
        # Initialize reflection layer
        print("\n[3/4] Setting up reflection layer...")
        self.reflection = RAGReflection(llm_provider=self.llm_provider)
        
        # Initialize evaluator
        print("\n[4/4] Setting up evaluator...")
        self.evaluator = RAGEvaluator(llm_provider=self.llm_provider)
        
        # Agent state
        self._conversation_history: List[AgentResponse] = []
        
        print("\n" + "=" * 60)
        print("✓ RAG Agent initialized!")
        print(f"  Knowledge base: {self.chatbot.vector_store.count()} chunks")
        print(f"  Confidence threshold: {self.config.min_confidence_threshold}")
        print(f"  Max iterations: {self.config.max_iterations}")
        print("=" * 60)
    
    def _load_llm_provider(self):
        """Load the tiered LLM provider from code_review module."""
        try:
            from code_review.llm_provider import TieredLLMProvider
            self.llm_provider = TieredLLMProvider()
            print("  ✓ Loaded TieredLLMProvider (multi-LLM fallback)")
        except ImportError:
            print("  ⚠ TieredLLMProvider not available, using basic generation")
            self.llm_provider = None
    
    def ask(self, question: str, verbose: Optional[bool] = None) -> AgentResponse:
        """
        Ask a question to the agent.
        
        This is the main entry point that triggers the agentic loop:
        1. Reason about the question
        2. Search knowledge base
        3. Generate answer
        4. Self-reflect and refine
        5. Evaluate final response
        
        Args:
            question: User's question
            verbose: Override config verbose setting
            
        Returns:
            AgentResponse with answer, sources, and metrics
        """
        verbose = verbose if verbose is not None else self.config.verbose
        
        if verbose:
            print("\n" + "=" * 60)
            print(f"Question: {question}")
            print("=" * 60)
        
        reasoning_steps = []
        tools_used = []
        
        # Step 1: Reason about the question
        if verbose:
            print("\n[Step 1] Reasoning about the question...")
        
        reasoning_steps.append(f"Received question: '{question}'")
        
        # Clarify if needed
        clarification = self.tools.execute_tool("clarify_question", question=question)
        if clarification.success and clarification.output.get("was_modified"):
            tools_used.append("clarify_question")
            clarified = clarification.output["clarified"]
            reasoning_steps.append(f"Clarified question to: '{clarified}'")
            question = clarified
        
        # Step 2: Search knowledge base
        if verbose:
            print("\n[Step 2] Searching knowledge base...")
        
        search_result = self.tools.execute_tool(
            "knowledge_search",
            query=question,
            top_k=self.config.top_k_retrieval
        )
        tools_used.append("knowledge_search")
        
        if not search_result.success:
            reasoning_steps.append(f"Search failed: {search_result.error}")
            return self._create_error_response(question, "Failed to search knowledge base")
        
        search_data = search_result.output
        context = search_data["context"]
        chunks = search_data["chunks"]
        
        reasoning_steps.append(f"Retrieved {len(chunks)} relevant chunks")
        
        if verbose:
            print(f"  Found {len(chunks)} relevant chunks")
            for chunk in chunks[:3]:
                print(f"    - {chunk['source']}: score={chunk['score']:.3f}")
        
        # Step 3: Generate answer
        if verbose:
            print("\n[Step 3] Generating answer...")
        
        answer = self._generate_answer(question, context)
        reasoning_steps.append("Generated initial answer")
        
        if verbose:
            print(f"  Generated answer ({len(answer)} chars)")
        
        # Step 4: Self-reflect and refine
        confidence = 0.7
        iterations = 1
        
        if self.config.use_reflection:
            if verbose:
                print("\n[Step 4] Self-reflecting on response...")
            
            reflection_result = self.reflection.reflect(
                question=question,
                answer=answer,
                context=context,
                sources=chunks
            )
            
            confidence = reflection_result.confidence
            reasoning_steps.append(f"Initial reflection: confidence={confidence:.2f}")
            
            if verbose:
                print(f"  Confidence: {confidence:.2f}")
                if reflection_result.issues:
                    print(f"  Issues: {', '.join(reflection_result.issues[:2])}")
            
            # Iterative refinement
            while reflection_result.should_refine and iterations < self.config.max_iterations:
                iterations += 1
                
                if verbose:
                    print(f"\n[Step 4.{iterations}] Refining answer (iteration {iterations})...")
                
                # Refine using LLM if available
                if self.llm_provider:
                    answer = self.reflection.refine_with_llm(
                        question=question,
                        answer=answer,
                        context=context,
                        reflection=reflection_result
                    )
                
                # Re-reflect
                reflection_result = self.reflection.reflect(
                    question=question,
                    answer=answer,
                    context=context,
                    sources=chunks
                )
                
                confidence = reflection_result.confidence
                reasoning_steps.append(f"Iteration {iterations}: confidence={confidence:.2f}")
                
                if verbose:
                    print(f"  New confidence: {confidence:.2f}")
        
        # Step 5: Evaluate final response
        evaluation = None
        if self.config.use_evaluation:
            if verbose:
                print("\n[Step 5] Evaluating response quality...")
            
            evaluation = self.evaluator.evaluate(
                question=question,
                answer=answer,
                context=context,
                sources=chunks
            )
            
            reasoning_steps.append(f"Evaluation: grade={evaluation.grade}, score={evaluation.overall_score:.2f}")
            
            if verbose:
                print(f"  Grade: {evaluation.grade} (score: {evaluation.overall_score:.2f})")
        
        # Step 6: Format sources
        sources_result = self.tools.execute_tool("provide_sources", chunks=chunks)
        tools_used.append("provide_sources")
        
        sources = chunks if not sources_result.success else [
            {"source": s, **sources_result.output["sources"].get(s, {})}
            for s in sources_result.output.get("sources", {}).keys()
        ]
        
        # Create response
        response = AgentResponse(
            question=question,
            answer=answer,
            sources=sources,
            confidence=confidence,
            evaluation=evaluation,
            reasoning_steps=reasoning_steps,
            tools_used=tools_used,
            reflection_summary=self.reflection.get_reflection_summary(),
            iterations=iterations
        )
        
        self._conversation_history.append(response)
        self.reflection.reset()
        self.tools.reset_history()
        
        if verbose:
            print("\n" + "=" * 60)
            print(f"✓ Response generated (confidence: {confidence:.2f})")
            print("=" * 60)
        
        return response
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using LLM."""
        if self.llm_provider:
            prompt = f"""Answer the following question based on the provided context.
Be comprehensive but concise. If the context doesn't fully answer the question, say so.

Context:
{context[:2000]}

Question: {question}

Answer:"""
            
            try:
                response = self.llm_provider.generate(prompt, max_tokens=500)
                return response.content.strip()
            except Exception as e:
                print(f"  Warning: LLM generation failed: {e}")
        
        # Fallback to base chatbot
        response = self.chatbot.ask(question)
        return response.answer
    
    def _create_error_response(self, question: str, error: str) -> AgentResponse:
        """Create an error response."""
        return AgentResponse(
            question=question,
            answer=f"I apologize, but I encountered an error: {error}",
            sources=[],
            confidence=0.0,
            reasoning_steps=[f"Error: {error}"]
        )
    
    def chat(self, question: str) -> str:
        """Simple chat interface - returns just the answer."""
        response = self.ask(question, verbose=False)
        return response.answer
    
    def interactive_chat(self):
        """Start an interactive chat session."""
        print("\n" + "=" * 60)
        print("RAG Agent - Interactive Mode")
        print("=" * 60)
        print("Ask questions about the knowledge base.")
        print("Commands: 'quit' to exit, 'history' to see past Q&As")
        print("-" * 60 + "\n")
        
        while True:
            try:
                question = input("You: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if question.lower() == 'history':
                    self._print_history()
                    continue
                
                response = self.ask(question, verbose=True)
                
                print(f"\nAgent: {response.answer}")
                
                # Show sources
                if response.sources:
                    source_names = list(set(
                        s.get("source", "Unknown") if isinstance(s, dict) else s.source
                        for s in response.sources[:5]
                    ))
                    print(f"\n[Sources: {', '.join(source_names)}]")
                
                print()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
    
    def _print_history(self):
        """Print conversation history."""
        if not self._conversation_history:
            print("\nNo conversation history yet.\n")
            return
        
        print("\n" + "-" * 40)
        print("Conversation History")
        print("-" * 40)
        
        for i, resp in enumerate(self._conversation_history[-5:], 1):
            print(f"\n[{i}] Q: {resp.question[:50]}...")
            print(f"    A: {resp.answer[:100]}...")
            print(f"    Confidence: {resp.confidence:.2f}")
        
        print("-" * 40 + "\n")
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "total_questions": len(self._conversation_history),
            "average_confidence": sum(r.confidence for r in self._conversation_history) / max(1, len(self._conversation_history)),
            "knowledge_base_size": self.chatbot.vector_store.count(),
            "evaluation_summary": self.evaluator.get_evaluation_summary()
        }
    
    def index_documents(self, force_reindex: bool = False) -> int:
        """Index knowledge base documents."""
        return self.chatbot.index_documents(force_reindex=force_reindex)


def create_agent(**kwargs) -> RAGAgent:
    """Factory function to create a RAG Agent."""
    return RAGAgent(**kwargs)


if __name__ == "__main__":
    # Quick test
    agent = RAGAgent()
    
    if agent.chatbot.is_indexed:
        response = agent.ask("What are the production Do's for RAG?")
        print(f"\nAnswer: {response.answer}")
        print(f"Confidence: {response.confidence}")
    else:
        print("Knowledge base is empty. Run: agent.index_documents()")
