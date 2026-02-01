#!/usr/bin/env python
"""
Quick test for RAG retrieval without audio playback.

This script tests the RAG retriever directly to verify
the knowledge base is being searched correctly.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import Retriever
from src.llm import LLMClient, LLMConfig
from src.llm.prompts import RAG_SYSTEM_PROMPT, NO_CONTEXT_PROMPT


def test_rag_responses():
    """Test RAG retrieval and LLM responses without audio."""
    
    print("=" * 60)
    print("RAG + LLM Integration Test (No Audio)")
    print("=" * 60)
    
    # Initialize retriever
    print("\nLoading retriever...")
    retriever = Retriever(relevance_threshold=0.3)
    print(f"  Documents in store: {retriever.store.count()}")
    
    # Initialize LLM
    print("Connecting to LLM...")
    llm = LLMClient(LLMConfig(max_tokens=256))
    if not llm.check_availability():
        print("LLM not available! Is Ollama running?")
        return False
    
    # Test queries
    test_queries = [
        "How do I change the filament on the 3D printer?",
        "What materials can I cut with the laser cutter?",
        "Where is the ICL located?",
        "What safety precautions should I follow for laser cutting?",
        "What is the build volume of the Ender CR M4?",
    ]
    
    results = []
    
    for query in test_queries:
        print("\n" + "-" * 60)
        print(f"QUERY: {query}")
        print("-" * 60)
        
        # Retrieve context
        retrieval_start = time.time()
        context = retriever.get_context(query, n_results=3)
        retrieval_time = time.time() - retrieval_start
        
        context_found = bool(context)
        print(f"\n📚 Context: {'Found' if context_found else 'None'} ({len(context)} chars)")
        print(f"   Retrieval time: {retrieval_time:.2f}s")
        
        if context:
            # Show first 200 chars of context
            print(f"   Preview: {context[:200]}...")
        
        # Generate response
        if context:
            system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
        else:
            system_prompt = NO_CONTEXT_PROMPT
        
        llm_start = time.time()
        response = llm.generate(query, system_prompt=system_prompt)
        llm_time = time.time() - llm_start
        
        print(f"\n🤖 Response ({llm_time:.2f}s):")
        print(f"   {response.text}")
        
        results.append({
            "query": query,
            "context_found": context_found,
            "context_length": len(context),
            "retrieval_time": retrieval_time,
            "llm_time": llm_time,
            "response": response.text
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    with_context = sum(1 for r in results if r["context_found"])
    avg_retrieval = sum(r["retrieval_time"] for r in results) / len(results)
    avg_llm = sum(r["llm_time"] for r in results) / len(results)
    
    print(f"\nQueries tested: {len(results)}")
    print(f"Found context: {with_context}/{len(results)}")
    print(f"Average retrieval time: {avg_retrieval:.2f}s")
    print(f"Average LLM time: {avg_llm:.2f}s")
    print(f"Average total: {avg_retrieval + avg_llm:.2f}s")
    
    print("\n" + "-" * 60)
    for r in results:
        status = "✅" if r["context_found"] else "❌"
        print(f"{status} {r['query'][:50]}")
    
    return with_context >= 4  # At least 4/5 should find context


def interactive_mode():
    """Interactive testing without audio."""
    print("=" * 60)
    print("RAG + LLM Interactive Test (No Audio)")
    print("Type 'quit' to exit")
    print("=" * 60)
    
    retriever = Retriever(relevance_threshold=0.3)
    llm = LLMClient(LLMConfig(max_tokens=256))
    
    if not llm.check_availability():
        print("LLM not available!")
        return
    
    print(f"\nLoaded {retriever.store.count()} documents")
    print("-" * 60)
    
    while True:
        try:
            query = input("\n🎤 You: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if not query:
                continue
            
            # Retrieve
            context = retriever.get_context(query, n_results=3)
            print(f"   📚 Found {len(context)} chars of context")
            
            # Generate
            if context:
                system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
            else:
                system_prompt = NO_CONTEXT_PROMPT
            
            response = llm.generate(query, system_prompt=system_prompt)
            print(f"\n🤖 Assistant: {response.text}")
            
        except KeyboardInterrupt:
            break
    
    print("\nGoodbye!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test RAG + LLM without audio")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    else:
        success = test_rag_responses()
        sys.exit(0 if success else 1)
