#!/usr/bin/env python
"""
Test script for the RAG-augmented pipeline.

This script tests the full pipeline with RAG integration,
asking questions about ICL equipment and verifying the 
responses use knowledge base context.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import VoicePipeline, PipelineConfig
from src.tts import TTSBackend


def test_rag_queries():
    """Test the pipeline with RAG-enabled queries."""
    
    print("=" * 60)
    print("RAG Pipeline Integration Test")
    print("=" * 60)
    
    # Create pipeline with RAG enabled
    config = PipelineConfig(
        use_rag=True,
        rag_n_results=3,
        rag_relevance_threshold=0.3,
        tts_backend=TTSBackend.PYTTSX3,
        tts_rate=180,  # Faster for testing
    )
    
    pipeline = VoicePipeline(config)
    
    print("\nInitializing pipeline...")
    if not pipeline.initialize():
        print("Failed to initialize pipeline!")
        return False
    
    # Test queries about ICL equipment
    test_queries = [
        "How do I change the filament on the 3D printer?",
        "What materials can I use with the laser cutter?",
        "Where is the ICL located?",
        "What are the safety precautions for using the laser cutter?",
        "What is the build volume of the Ender 3 V3 KE?",
    ]
    
    results = []
    
    for query in test_queries:
        print("\n" + "=" * 60)
        print(f"QUERY: {query}")
        print("=" * 60)
        
        try:
            turn = pipeline.process_text(query)
            
            if turn:
                results.append({
                    "query": query,
                    "response": turn.assistant_text,
                    "retrieval_time": turn.metrics.retrieval_time,
                    "llm_time": turn.metrics.llm_time,
                    "context_found": turn.metrics.context_found,
                    "success": True
                })
            else:
                results.append({
                    "query": query,
                    "success": False
                })
                
        except Exception as e:
            print(f"Error processing query: {e}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r.get("success"))
    with_context = sum(1 for r in results if r.get("context_found"))
    
    print(f"\nQueries tested: {len(results)}")
    print(f"Successful: {successful}/{len(results)}")
    print(f"Found relevant context: {with_context}/{len(results)}")
    
    if results:
        avg_retrieval = sum(r.get("retrieval_time", 0) for r in results) / len(results)
        avg_llm = sum(r.get("llm_time", 0) for r in results) / len(results)
        print(f"\nAverage retrieval time: {avg_retrieval:.3f}s")
        print(f"Average LLM time: {avg_llm:.2f}s")
    
    print("\n" + "-" * 60)
    for r in results:
        status = "✅" if r.get("context_found") else "❌"
        print(f"{status} {r['query'][:50]}...")
        if r.get("response"):
            print(f"   → {r['response'][:100]}...")
    
    pipeline.shutdown()
    
    return successful == len(results)


def interactive_mode():
    """Interactive testing mode."""
    print("=" * 60)
    print("RAG Pipeline Interactive Mode")
    print("Type 'quit' to exit")
    print("=" * 60)
    
    config = PipelineConfig(
        use_rag=True,
        rag_n_results=3,
        tts_backend=TTSBackend.PYTTSX3,
        tts_rate=160,
    )
    
    pipeline = VoicePipeline(config)
    
    print("\nInitializing pipeline...")
    if not pipeline.initialize():
        print("Failed to initialize pipeline!")
        return
    
    print("\nReady! Ask questions about ICL equipment.")
    print("-" * 60)
    
    while True:
        try:
            query = input("\n🎤 You: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if not query:
                continue
            
            pipeline.process_text(query)
            
        except KeyboardInterrupt:
            break
    
    pipeline.shutdown()
    print("\nGoodbye!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test RAG-augmented pipeline")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    else:
        success = test_rag_queries()
        sys.exit(0 if success else 1)
