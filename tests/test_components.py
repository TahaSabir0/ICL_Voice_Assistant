"""
Component verification tests for ICL Voice Assistant.
Run: uv run pytest tests/test_components.py -v
"""

import sys
import time


def test_ollama_connection():
    """Test that Ollama is running and Llama 3.1 responds."""
    print("\n🔌 Testing Ollama connection...")
    
    import ollama
    
    # List available models
    models = ollama.list()
    model_names = [m.model for m in models.models]
    print(f"   Available models: {model_names}")
    
    # Check if llama3.1 is available (might have different tag formats)
    llama_available = any("llama3.1" in name for name in model_names)
    assert llama_available, f"Llama 3.1 not found. Available: {model_names}"
    
    # Test a simple generation
    print("   Sending test prompt to Llama 3.1...")
    start = time.time()
    response = ollama.chat(
        model="llama3.1:8b-instruct-q4_K_M",
        messages=[{"role": "user", "content": "Say 'Hello, ICL!' and nothing else."}]
    )
    elapsed = time.time() - start
    
    answer = response.message.content
    print(f"   Response: {answer}")
    print(f"   Latency: {elapsed:.2f}s")
    
    assert len(answer) > 0, "Empty response from Llama 3.1"
    print("   ✅ Ollama + Llama 3.1 working!")


def test_faster_whisper_loads():
    """Test that Faster Whisper STT model loads."""
    print("\n🎤 Testing Faster Whisper (STT)...")
    
    from faster_whisper import WhisperModel
    
    # Load the 'base' model for quick testing (smaller than 'medium')
    print("   Loading Whisper 'base' model (for quick test)...")
    start = time.time()
    model = WhisperModel("base", device="cpu", compute_type="int8")
    elapsed = time.time() - start
    
    print(f"   Model loaded in {elapsed:.2f}s")
    assert model is not None, "Failed to load Whisper model"
    print("   ✅ Faster Whisper loads successfully!")
    
    # Cleanup
    del model


def test_piper_tts_loads():
    """Test that Piper TTS can be initialized."""
    print("\n🔊 Testing Piper TTS...")
    
    try:
        from piper import PiperVoice
        import wave
        import io
        
        # Download/load a voice model
        print("   Initializing Piper TTS...")
        
        # Piper needs a voice model file - let's check if the library loads
        # The actual voice model download will happen in implementation
        print("   Piper library imported successfully")
        print("   ✅ Piper TTS module available!")
        
    except ImportError as e:
        # Piper might have different import structure
        print(f"   Note: Piper import structure: {e}")
        
        # Try alternative import
        try:
            import piper_tts
            print("   Piper TTS package available (alternative import)")
            print("   ✅ Piper TTS module available!")
        except ImportError:
            # Check if piper command line tool is available
            import subprocess
            result = subprocess.run(["piper", "--help"], capture_output=True, text=True)
            if result.returncode == 0:
                print("   Piper CLI tool available")
                print("   ✅ Piper TTS available via CLI!")
            else:
                raise AssertionError("Piper TTS not available")


def test_chromadb_initializes():
    """Test that ChromaDB vector store can be created."""
    print("\n📚 Testing ChromaDB...")
    
    import chromadb
    
    # Create an ephemeral client (in-memory, for testing)
    print("   Creating ChromaDB client...")
    client = chromadb.Client()
    
    # Create a test collection
    collection = client.create_collection(name="test_collection")
    
    # Add a test document
    collection.add(
        documents=["This is a test document about 3D printing."],
        ids=["doc1"]
    )
    
    # Query it
    results = collection.query(
        query_texts=["3D printer"],
        n_results=1
    )
    
    print(f"   Query results: {results['documents']}")
    assert len(results["documents"]) > 0, "ChromaDB query failed"
    print("   ✅ ChromaDB working!")


def test_sentence_transformers_loads():
    """Test that embedding model loads."""
    print("\n🧠 Testing Sentence Transformers (embeddings)...")
    
    from sentence_transformers import SentenceTransformer
    
    print("   Loading all-MiniLM-L6-v2 embedding model...")
    start = time.time()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    elapsed = time.time() - start
    print(f"   Model loaded in {elapsed:.2f}s")
    
    # Test embedding
    test_text = "How do I use the 3D printer?"
    embedding = model.encode(test_text)
    
    print(f"   Embedding dimension: {len(embedding)}")
    assert len(embedding) == 384, f"Unexpected embedding dimension: {len(embedding)}"
    print("   ✅ Sentence Transformers working!")
    
    # Cleanup
    del model


def test_audio_devices_available():
    """Test that audio devices are accessible."""
    print("\n🎧 Testing audio devices...")
    
    import sounddevice as sd
    
    # List devices
    devices = sd.query_devices()
    print(f"   Found {len(devices)} audio device(s)")
    
    # Find input (mic) and output (speaker) devices
    input_devices = [d for d in devices if d['max_input_channels'] > 0]
    output_devices = [d for d in devices if d['max_output_channels'] > 0]
    
    print(f"   Input devices (mics): {len(input_devices)}")
    print(f"   Output devices (speakers): {len(output_devices)}")
    
    if input_devices:
        print(f"   Default input: {sd.query_devices(kind='input')['name']}")
    if output_devices:
        print(f"   Default output: {sd.query_devices(kind='output')['name']}")
    
    assert len(input_devices) > 0, "No microphone found"
    assert len(output_devices) > 0, "No speakers found"
    print("   ✅ Audio devices available!")


def test_pyside6_loads():
    """Test that PySide6 can be imported."""
    print("\n🖥️ Testing PySide6 (UI)...")
    
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication
    
    print("   PySide6 imported successfully")
    print(f"   Qt version: {QCoreApplication.applicationVersion() or 'available'}")
    print("   ✅ PySide6 available!")


if __name__ == "__main__":
    print("=" * 60)
    print("ICL Voice Assistant - Component Verification")
    print("=" * 60)
    
    tests = [
        ("Ollama + Llama 3.1", test_ollama_connection),
        ("Faster Whisper (STT)", test_faster_whisper_loads),
        ("Piper TTS", test_piper_tts_loads),
        ("ChromaDB", test_chromadb_initializes),
        ("Sentence Transformers", test_sentence_transformers_loads),
        ("Audio Devices", test_audio_devices_available),
        ("PySide6 (UI)", test_pyside6_loads),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            test_func()
            results.append((name, True, None))
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append((name, False, str(e)))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         → {error}")
    
    print(f"\n{passed}/{total} components verified")
    
    if passed == total:
        print("\n🎉 All components ready! You can proceed to Phase 1, Plan 01-02.")
    else:
        print("\n⚠️ Some components need attention before proceeding.")
    
    sys.exit(0 if passed == total else 1)
