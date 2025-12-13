"""
Vector Store Module
Uses ChromaDB for storing and querying vector embeddings.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path


class VectorStore:
    """
    ChromaDB-based vector store for RAG.
    Provides persistent storage and similarity search.
    """
    
    def __init__(
        self,
        collection_name: str = "rag_knowledge_base",
        persist_directory: str = "./chroma_db"
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
        """
        persist_path = Path(persist_directory)
        persist_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(path=str(persist_path))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        self.collection_name = collection_name
        print(f"✓ Initialized vector store: {collection_name}")
        print(f"  Existing documents: {self.collection.count()}")
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the vector store.
        
        Args:
            texts: List of text content
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs
        """
        if ids is None:
            # Generate unique IDs
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(texts))]
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        # Batch processing for large datasets (ChromaDB max batch is ~5000)
        BATCH_SIZE = 5000
        total = len(texts)
        
        for start in range(0, total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total)
            batch_texts = texts[start:end]
            batch_embeddings = embeddings[start:end]
            batch_metadatas = metadatas[start:end]
            batch_ids = ids[start:end]
            
            self.collection.add(
                documents=batch_texts,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            print(f"  Added batch {start//BATCH_SIZE + 1}: {len(batch_texts)} documents")
        
        print(f"✓ Added {len(texts)} documents to vector store")
        print(f"  Total documents: {self.collection.count()}")
    
    def add_chunks(self, chunks: List, embeddings: List[List[float]]):
        """
        Add TextChunk objects to the vector store.
        
        Args:
            chunks: List of TextChunk objects
            embeddings: List of embedding vectors
        """
        texts = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "source": chunk.source,
                "chunk_id": chunk.chunk_id,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char
            }
            for chunk in chunks
        ]
        ids = [f"{chunk.source}_{chunk.chunk_id}" for chunk in chunks]
        
        self.add_documents(texts, embeddings, metadatas, ids)
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.
        
        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with documents, metadatas, distances, and ids
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else []
        }
    
    def clear(self):
        """Clear all documents from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✓ Cleared collection: {self.collection_name}")
    
    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()


if __name__ == "__main__":
    # Test the vector store
    import numpy as np
    
    store = VectorStore(collection_name="test_collection", persist_directory="./test_chroma")
    
    # Add some test documents
    texts = [
        "RAG stands for Retrieval-Augmented Generation",
        "Vector databases store embeddings",
        "ChromaDB is a popular vector database"
    ]
    
    # Generate random embeddings for testing (in production, use real embeddings)
    embeddings = np.random.rand(3, 384).tolist()
    
    store.add_documents(texts, embeddings)
    
    # Query with a random embedding
    query_embedding = np.random.rand(384).tolist()
    results = store.query(query_embedding, n_results=2)
    
    print("\nQuery results:")
    for doc, meta, dist in zip(results["documents"], results["metadatas"], results["distances"]):
        print(f"  Distance: {dist:.4f}")
        print(f"  Text: {doc[:50]}...")
        print()
