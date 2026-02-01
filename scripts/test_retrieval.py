#!/usr/bin/env python3
"""
Test the RAG retrieval system with sample queries.

Usage:
    python scripts/test_retrieval.py
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import get_retriever


def test_retrieval():
    """Test retrieval with sample ICL queries."""
    
    print("=" * 60)
    print("RAG RETRIEVAL TEST")
    print("=" * 60)
    
    retriever = get_retriever()
    
    # Sample queries
    test_queries = [
        "How do I change the filament on the 3D printer?",
        "What materials can I cut with the laser cutter?",
        "What are the safety precautions for the laser cutter?",
        "How do I use the embroidery machine?",
        "What VR headsets are available in the ICL?",
        "What are the build dimensions of the Ender 3?",
        "Where is the ICL located?",
        "How do I slice a file for 3D printing?",
        "What is the vinyl cutter cutting area?",
        "How do I set up the HTC Vive?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {query}")
        print("=" * 60)
        
        results = retriever.search(query, n_results=3)
        
        if not results:
            print("❌ No relevant results found")
            continue
        
        for j, r in enumerate(results, 1):
            print(f"\n--- Result {j} ({r.relevance:.1%} relevant) ---")
            print(f"Source: {r.title} > {r.section}")
            print(f"Category: {r.category}")
            print(f"Content preview: {r.content[:300]}...")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    # Summary stats
    stats = retriever.store.get_stats()
    print(f"\nVector store stats:")
    print(f"  Documents: {stats['document_count']}")
    print(f"  Embedding dim: {stats['embedding_dimension']}")


def interactive_search():
    """Interactive search mode."""
    print("\n" + "=" * 60)
    print("INTERACTIVE SEARCH MODE")
    print("Type 'quit' to exit")
    print("=" * 60)
    
    retriever = get_retriever()
    
    while True:
        query = input("\nEnter query: ").strip()
        if query.lower() in ('quit', 'exit', 'q'):
            break
        if not query:
            continue
        
        results = retriever.search(query, n_results=3)
        
        if not results:
            print("No relevant results found")
            continue
        
        print(f"\nFound {len(results)} results:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r.relevance:.0%}] {r.title} - {r.section}")
            print(f"   {r.content[:200]}...")
            print()
        
        # Show context that would be sent to LLM
        print("-" * 40)
        print("Context for LLM:")
        print("-" * 40)
        context = retriever.get_context(query)
        print(context[:1000] + "..." if len(context) > 1000 else context)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Run in interactive mode")
    args = parser.parse_args()
    
    if args.interactive:
        interactive_search()
    else:
        test_retrieval()
