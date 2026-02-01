"""
Retrieval service for RAG.

Provides a high-level interface for searching the knowledge base.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .vectorstore import VectorStore, get_vector_store, DEFAULT_STORE_PATH


@dataclass
class RetrievalResult:
    """A single retrieval result."""
    
    content: str
    title: str
    section: str
    category: str
    source: str
    relevance: float
    
    def __str__(self) -> str:
        return f"[{self.title} - {self.section}] ({self.relevance:.2%})\n{self.content[:200]}..."


class Retriever:
    """
    High-level retrieval interface for the knowledge base.
    
    Wraps the vector store and provides convenience methods
    for RAG-style retrieval.
    """
    
    def __init__(
        self,
        store_path: Optional[Path] = None,
        store: Optional[VectorStore] = None,
        default_n_results: int = 5,
        relevance_threshold: float = 0.3
    ):
        # Use provided store, or create/get one from path
        if store is not None:
            self.store = store
        else:
            self.store = VectorStore(persist_directory=store_path or DEFAULT_STORE_PATH)
        self.default_n_results = default_n_results
        self.relevance_threshold = relevance_threshold
    
    def search(
        self,
        query: str,
        n_results: Optional[int] = None,
        category: Optional[str] = None,
        include_low_relevance: bool = False
    ) -> list[RetrievalResult]:
        """
        Search for relevant content.
        
        Args:
            query: Search query
            n_results: Number of results to return
            category: Filter by category (3d_printing, laser_cutting, etc.)
            include_low_relevance: Include results below threshold
            
        Returns:
            List of RetrievalResult objects
        """
        n_results = n_results or self.default_n_results
        
        raw_results = self.store.search(
            query=query,
            n_results=n_results,
            filter_category=category
        )
        
        results = []
        for r in raw_results:
            relevance = r.get('relevance', 0)
            
            # Filter low relevance unless requested
            if not include_low_relevance and relevance < self.relevance_threshold:
                continue
            
            results.append(RetrievalResult(
                content=r['content'],
                title=r['metadata'].get('title', 'Unknown'),
                section=r['metadata'].get('section', 'Unknown'),
                category=r['metadata'].get('category', 'unknown'),
                source=r['metadata'].get('source', 'unknown'),
                relevance=relevance
            ))
        
        return results
    
    def get_context(
        self,
        query: str,
        n_results: Optional[int] = None,
        max_context_length: int = 4000
    ) -> str:
        """
        Get formatted context for LLM augmentation.
        
        Args:
            query: User query
            n_results: Number of results to include
            max_context_length: Maximum character length of context
            
        Returns:
            Formatted context string for LLM
        """
        results = self.search(query, n_results)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for r in results:
            # Format this result
            part = f"## {r.title} - {r.section}\n\n{r.content}\n"
            
            # Check length limit
            if current_length + len(part) > max_context_length:
                # Try to truncate
                remaining = max_context_length - current_length
                if remaining > 200:  # Only include if meaningful
                    part = f"## {r.title} - {r.section}\n\n{r.content[:remaining-50]}...\n"
                    context_parts.append(part)
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return "\n".join(context_parts)
    
    def is_relevant_query(self, query: str, threshold: float = 0.4) -> bool:
        """
        Check if the query is relevant to the knowledge base.
        
        Args:
            query: User query
            threshold: Minimum relevance score
            
        Returns:
            True if query matches something in the knowledge base
        """
        results = self.search(query, n_results=1, include_low_relevance=True)
        return bool(results) and results[0].relevance >= threshold


# Global retriever instance
_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    """Get or create the global retriever."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
