"""
Benchmark script for the ICL Voice Assistant pipeline.

Tests end-to-end latency with predefined questions to verify
the <8 second response time target.
"""

import time
import sys
from typing import List, Dict

from src.pipeline import VoicePipeline, PipelineConfig, PipelineMetrics
from src.llm import LLMClient, LLMConfig
from src.stt import SpeechToText, STTConfig
from src.tts import TextToSpeech, TTSConfig


# Test questions for benchmarking
BENCHMARK_QUESTIONS = [
    "What 3D printers do you have?",
    "How do I use the laser cutter?",
    "Is the lab open on weekends?",
    "What materials can I cut with the laser?",
    "How do I get started with CNC?",
]


def benchmark_llm_only():
    """Benchmark just the LLM response time."""
    print("\n" + "=" * 60)
    print("LLM-Only Benchmark")
    print("=" * 60)
    
    config = LLMConfig(
        model="llama3.1:8b-instruct-q4_K_M",
        max_tokens=256
    )
    llm = LLMClient(config)
    
    if not llm.check_availability():
        print("ERROR: LLM not available")
        return
    
    times = []
    for question in BENCHMARK_QUESTIONS:
        print(f"\n📝 Q: {question}")
        
        start = time.time()
        response = llm.generate(question)
        elapsed = time.time() - start
        times.append(elapsed)
        
        print(f"   A: {response.text[:100]}...")
        print(f"   ⏱️  Time: {elapsed:.2f}s")
    
    avg_time = sum(times) / len(times)
    print(f"\n📊 LLM Average: {avg_time:.2f}s (min: {min(times):.2f}s, max: {max(times):.2f}s)")
    
    return times


def benchmark_tts_only():
    """Benchmark just the TTS synthesis time."""
    print("\n" + "=" * 60)
    print("TTS-Only Benchmark")
    print("=" * 60)
    
    tts = TextToSpeech()
    tts.load_voice()
    
    test_texts = [
        "We have several 3D printers including Prusa and Ender models.",
        "The laser cutter is great for cutting wood, acrylic, and leather.",
        "The lab is open 24/7 on the first floor of Plank Gym.",
    ]
    
    times = []
    for text in test_texts:
        print(f"\n📝 Text: {text[:50]}...")
        
        start = time.time()
        result = tts.synthesize(text)
        elapsed = time.time() - start
        times.append(elapsed)
        
        print(f"   Duration: {result.duration:.2f}s audio")
        print(f"   ⏱️  Synthesis time: {elapsed:.2f}s")
        print(f"   Realtime factor: {result.realtime_factor:.1f}x")
    
    avg_time = sum(times) / len(times)
    print(f"\n📊 TTS Average: {avg_time:.2f}s")
    
    tts.unload_voice()
    return times


def benchmark_full_pipeline(skip_audio: bool = True):
    """
    Benchmark the full pipeline (optionally skipping audio).
    
    Args:
        skip_audio: If True, use text input instead of recording.
    """
    print("\n" + "=" * 60)
    print("Full Pipeline Benchmark")
    print("=" * 60)
    
    config = PipelineConfig(
        stt_model="base",
        llm_max_tokens=256,
        tts_rate=160
    )
    pipeline = VoicePipeline(config)
    
    print("\nInitializing pipeline...")
    if not pipeline.initialize():
        print("ERROR: Failed to initialize pipeline")
        return
    
    results: List[Dict] = []
    
    for question in BENCHMARK_QUESTIONS:
        print(f"\n{'=' * 40}")
        result = pipeline.process_text(question)
        
        if result:
            metrics = result.metrics.to_dict()
            metrics["question"] = question
            results.append(metrics)
    
    # Summary
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    
    if results:
        processing_times = [r["processing"] for r in results]
        avg_processing = sum(processing_times) / len(processing_times)
        
        print(f"\n📊 Processing Time (STT + LLM + TTS):")
        print(f"   Average: {avg_processing:.2f}s")
        print(f"   Min: {min(processing_times):.2f}s")
        print(f"   Max: {max(processing_times):.2f}s")
        
        # Check against target
        target = 8.0
        if avg_processing < target:
            print(f"\n✅ PASS: Average {avg_processing:.2f}s < {target}s target")
        else:
            print(f"\n❌ FAIL: Average {avg_processing:.2f}s > {target}s target")
        
        # Detailed breakdown
        print("\n📋 Detailed Breakdown:")
        print("-" * 60)
        
        llm_times = [r["llm"] for r in results]
        tts_times = [r["tts"] for r in results]
        
        print(f"   LLM:  avg {sum(llm_times)/len(llm_times):.2f}s")
        print(f"   TTS:  avg {sum(tts_times)/len(tts_times):.2f}s")
        
        print("\n📝 Per-Question Results:")
        for r in results:
            print(f"   {r['question'][:40]}...")
            print(f"      → {r['processing']:.2f}s (LLM: {r['llm']:.2f}s, TTS: {r['tts']:.2f}s)")
    
    pipeline.shutdown()
    return results


def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("ICL Voice Assistant - Benchmarks")
    print("=" * 60)
    
    # Run benchmarks
    benchmark_llm_only()
    benchmark_tts_only()
    benchmark_full_pipeline(skip_audio=True)
    
    print("\n" + "=" * 60)
    print("Benchmarks Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
