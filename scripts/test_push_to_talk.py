#!/usr/bin/env python
"""
Push-to-Talk RAG Test

This script provides a manual recording control where:
- Press 'y' + Enter to start recording
- Press 'x' + Enter to stop recording
- The system then transcribes, retrieves context, and responds
"""

import sys
import time
import threading
import queue
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import sounddevice as sd

from src.stt import SpeechToText, STTConfig
from src.llm import LLMClient, LLMConfig
from src.tts import TextToSpeech, TTSConfig, TTSBackend
from src.audio import AudioPlayback
from src.rag import Retriever
from src.llm.prompts import RAG_SYSTEM_PROMPT, NO_CONTEXT_PROMPT


class PushToTalkRecorder:
    """Records audio until manually stopped."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio chunk."""
        if self.is_recording:
            self.audio_queue.put(indata.copy())
    
    def start(self):
        """Start recording."""
        self.audio_queue = queue.Queue()
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            callback=self._audio_callback,
            blocksize=1024
        )
        self.stream.start()
    
    def stop(self) -> np.ndarray:
        """Stop recording and return audio."""
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Collect all audio chunks
        chunks = []
        while not self.audio_queue.empty():
            chunks.append(self.audio_queue.get())
        
        if chunks:
            audio = np.concatenate(chunks, axis=0).flatten()
            return audio
        return np.array([], dtype=np.float32)


def main():
    print("=" * 60)
    print("Push-to-Talk RAG Voice Assistant")
    print("=" * 60)
    print("\nControls:")
    print("  'y' + Enter  →  Start recording")
    print("  'x' + Enter  →  Stop recording")
    print("  'q' + Enter  →  Quit")
    print("-" * 60)
    
    # Initialize components
    print("\n⏳ Loading components...")
    
    print("  Loading STT (Whisper)...")
    stt = SpeechToText(STTConfig(model_size="base", device="auto"))
    stt.load_model()
    
    print("  Loading LLM...")
    llm = LLMClient(LLMConfig(max_tokens=256))
    if not llm.check_availability():
        print("❌ LLM not available! Is Ollama running?")
        return
    
    print("  Loading TTS...")
    tts = TextToSpeech(TTSConfig(backend=TTSBackend.PYTTSX3, rate=160))
    tts.load_voice()
    
    print("  Loading RAG retriever...")
    try:
        retriever = Retriever(relevance_threshold=0.3)
        print(f"    {retriever.store.count()} documents loaded")
        rag_enabled = True
    except Exception as e:
        print(f"    RAG not available: {e}")
        retriever = None
        rag_enabled = False
    
    playback = AudioPlayback()
    recorder = PushToTalkRecorder()
    
    print("\n✅ Ready!")
    print("=" * 60)
    
    while True:
        print("\n🎤 Press 'y' + Enter to start recording (or 'q' to quit):")
        
        cmd = input().strip().lower()
        
        if cmd == 'q':
            print("\nGoodbye!")
            break
        
        if cmd != 'y':
            print("  (Enter 'y' to record, 'q' to quit)")
            continue
        
        # Start recording
        print("\n🔴 RECORDING... (press 'x' + Enter to stop)")
        recorder.start()
        record_start = time.time()
        
        # Wait for stop command
        while True:
            stop_cmd = input().strip().lower()
            if stop_cmd == 'x':
                break
            print("  (Press 'x' + Enter to stop recording)")
        
        # Stop recording
        audio = recorder.stop()
        record_duration = time.time() - record_start
        
        print(f"\n⏹️  Stopped. Recorded {record_duration:.1f} seconds")
        
        if len(audio) < 1000:
            print("  ⚠️  Recording too short, try again")
            continue
        
        # Transcribe
        print("\n📝 Transcribing...")
        stt_start = time.time()
        result = stt.transcribe(audio)
        stt_time = time.time() - stt_start
        
        user_text = result.text.strip()
        print(f"   You said: \"{user_text}\"")
        print(f"   (STT took {stt_time:.2f}s)")
        
        if not user_text:
            print("  ⚠️  No speech detected, try again")
            continue
        
        # RAG retrieval
        context = ""
        if retriever:
            print("\n🔍 Searching knowledge base...")
            retrieval_start = time.time()
            context = retriever.get_context(user_text, n_results=3)
            retrieval_time = time.time() - retrieval_start
            
            if context:
                print(f"   Found {len(context)} chars of relevant context")
            else:
                print("   No relevant context found")
            print(f"   (Retrieval took {retrieval_time:.2f}s)")
        
        # Generate response
        print("\n🤔 Generating response...")
        llm_start = time.time()
        
        if context:
            system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
        else:
            system_prompt = NO_CONTEXT_PROMPT if rag_enabled else None
        
        response = llm.generate(user_text, system_prompt=system_prompt)
        llm_time = time.time() - llm_start
        
        assistant_text = response.text.strip()
        print(f"\n🤖 Assistant: {assistant_text}")
        print(f"   (LLM took {llm_time:.2f}s)")
        
        # Speak response
        print("\n🔊 Speaking...")
        tts_start = time.time()
        tts_result = tts.synthesize(assistant_text)
        tts_time = time.time() - tts_start
        
        playback.play(tts_result.audio, sample_rate=tts_result.sample_rate, blocking=True)
        
        # Summary
        total_time = stt_time + (retrieval_time if retriever else 0) + llm_time + tts_time
        print(f"\n⏱️  Total processing: {total_time:.2f}s")
        print("-" * 60)


if __name__ == "__main__":
    main()
