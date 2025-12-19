"""
RAG Agent Tools

Tool functions that the agent can call:
- knowledge_search: Search the RAG knowledge base
- clarify_question: Rephrase ambiguous questions
- summarize_context: Summarize long contexts
- provide_sources: Format source citations
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_chatbot.retriever import Retriever, RetrievedChunk
from rag_chatbot.embedder import Embedder
from rag_chatbot.vector_store import VectorStore


@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """Definition of an available tool."""
    name: str
    description: str
    parameters: Dict[str, str]
    

class RAGTools:
    """
    Collection of tools for the RAG Agent.
    
    Each tool follows a standard interface:
    - Takes specific parameters
    - Returns a ToolResult
    - Is callable by the agent's reasoning loop
    """
    
    TOOL_DEFINITIONS = [
        ToolDefinition(
            name="knowledge_search",
            description="Search the knowledge base for information relevant to a query",
            parameters={"query": "The search query string", "top_k": "Number of results (default 5)"}
        ),
        ToolDefinition(
            name="clarify_question",
            description="Rephrase an ambiguous question into a clearer form",
            parameters={"question": "The original question", "context": "Optional context"}
        ),
        ToolDefinition(
            name="summarize_context",
            description="Summarize long retrieved contexts into key points",
            parameters={"context": "The context text to summarize"}
        ),
        ToolDefinition(
            name="provide_sources",
            description="Format source citations from retrieved chunks",
            parameters={"chunks": "List of retrieved chunks"}
        ),
    ]
    
    def __init__(
        self,
        retriever: Retriever,
        llm_provider=None
    ):
        """
        Initialize RAG tools.
        
        Args:
            retriever: Retriever instance for knowledge base search
            llm_provider: Optional LLM provider for clarification/summarization
        """
        self.retriever = retriever
        self.llm_provider = llm_provider
        self._tool_call_count = 0
        self._tool_history: List[ToolResult] = []
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with their definitions."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters
            }
            for t in self.TOOL_DEFINITIONS
        ]
    
    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters
            
        Returns:
            ToolResult with output or error
        """
        self._tool_call_count += 1
        
        tool_methods = {
            "knowledge_search": self.knowledge_search,
            "clarify_question": self.clarify_question,
            "summarize_context": self.summarize_context,
            "provide_sources": self.provide_sources,
        }
        
        if tool_name not in tool_methods:
            result = ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Unknown tool: {tool_name}"
            )
        else:
            try:
                output = tool_methods[tool_name](**kwargs)
                result = ToolResult(
                    tool_name=tool_name,
                    success=True,
                    output=output
                )
            except Exception as e:
                result = ToolResult(
                    tool_name=tool_name,
                    success=False,
                    output=None,
                    error=str(e)
                )
        
        self._tool_history.append(result)
        return result
    
    def knowledge_search(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            Dict with chunks and formatted context
        """
        chunks = self.retriever.retrieve(query, top_k=top_k)
        context = self.retriever.retrieve_with_context(query, top_k=top_k)
        
        return {
            "query": query,
            "num_results": len(chunks),
            "chunks": [
                {
                    "text": chunk.text,
                    "source": chunk.source,
                    "score": chunk.relevance_score
                }
                for chunk in chunks
            ],
            "context": context
        }
    
    def clarify_question(
        self,
        question: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Rephrase an ambiguous question for clearer understanding.
        
        Args:
            question: Original question
            context: Optional context to help clarification
            
        Returns:
            Dict with original and clarified question
        """
        if self.llm_provider:
            prompt = f"""Rephrase this question to be clearer and more specific.
            
Original question: {question}
{"Context: " + context if context else ""}

Provide a clearer version of the question that:
1. Is more specific
2. Can be answered with available information
3. Maintains the original intent

Clarified question:"""
            
            try:
                response = self.llm_provider.generate(prompt, max_tokens=100)
                clarified = response.content.strip()
            except:
                clarified = question
        else:
            # Simple rule-based clarification
            clarified = question
            if not question.endswith("?"):
                clarified = question + "?"
            # Remove filler words
            filler_words = ["um", "uh", "like", "you know"]
            for filler in filler_words:
                clarified = clarified.replace(f" {filler} ", " ")
        
        return {
            "original": question,
            "clarified": clarified,
            "was_modified": clarified != question
        }
    
    def summarize_context(
        self,
        context: str,
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Summarize long context into key points.
        
        Args:
            context: Context text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Dict with original length, summary, and key points
        """
        original_length = len(context)
        
        if self.llm_provider and original_length > max_length:
            prompt = f"""Summarize the following text into key bullet points:

{context[:2000]}

Provide a concise summary with the most important points:"""
            
            try:
                response = self.llm_provider.generate(prompt, max_tokens=200)
                summary = response.content.strip()
            except:
                # Fallback: truncate
                summary = context[:max_length] + "..."
        else:
            if original_length > max_length:
                summary = context[:max_length] + "..."
            else:
                summary = context
        
        # Extract key points (simple heuristic)
        key_points = []
        for line in summary.split("\n"):
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("•") or line.startswith("*")):
                key_points.append(line.lstrip("-•* "))
        
        return {
            "original_length": original_length,
            "summary_length": len(summary),
            "summary": summary,
            "key_points": key_points,
            "was_truncated": original_length > max_length
        }
    
    def provide_sources(
        self,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format source citations from retrieved chunks.
        
        Args:
            chunks: List of chunk dictionaries with source info
            
        Returns:
            Dict with formatted citations
        """
        sources = {}
        for chunk in chunks:
            source = chunk.get("source", "Unknown")
            score = chunk.get("score", 0)
            
            if source not in sources:
                sources[source] = {
                    "count": 0,
                    "avg_score": 0,
                    "scores": []
                }
            sources[source]["count"] += 1
            sources[source]["scores"].append(score)
        
        # Calculate averages
        for source, info in sources.items():
            info["avg_score"] = sum(info["scores"]) / len(info["scores"])
            del info["scores"]
        
        # Format citations
        citations = []
        for source, info in sorted(sources.items(), key=lambda x: -x[1]["avg_score"]):
            citations.append(f"[{source}] (relevance: {info['avg_score']:.2f}, {info['count']} chunks)")
        
        return {
            "num_sources": len(sources),
            "sources": sources,
            "formatted_citations": citations
        }
    
    def get_tool_history(self) -> List[Dict[str, Any]]:
        """Get history of tool calls."""
        return [
            {
                "tool": r.tool_name,
                "success": r.success,
                "error": r.error
            }
            for r in self._tool_history
        ]
    
    def reset_history(self):
        """Reset tool call history."""
        self._tool_call_count = 0
        self._tool_history = []
