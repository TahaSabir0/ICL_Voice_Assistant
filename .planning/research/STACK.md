# Stack Research

**Domain:** Local AI Voice Assistant with RAG
**Researched:** 2026-01-30
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Application language | De facto standard for ML/AI pipelines; best library ecosystem for STT, LLM, TTS, and RAG |
| Faster Whisper | 1.1+ | Speech-to-text | CTranslate2-optimized Whisper — 4x faster than OpenAI Whisper with same accuracy, lower VRAM |
| Ollama | 0.5+ | Local LLM serving | Simple model management, OpenAI-compatible API, handles VRAM, supports quantized models |
| Llama 3.1 8B (Q4_K_M) | 8B params | LLM for answer generation | Best quality-to-VRAM ratio at 8B; Q4 quantization fits ~5GB VRAM; strong instruction following |
| Piper TTS | 1.2+ | Text-to-speech | Fast local TTS, runs on CPU, natural-sounding voices, low resource usage |
| ChromaDB | 0.5+ | Vector database for RAG | Embedded vector DB, no server needed, simple Python API, persistent storage |
| sentence-transformers | 3.0+ | Embedding model | all-MiniLM-L6-v2 for embeddings — fast, accurate, tiny VRAM footprint (~100MB) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| LangChain | 0.3+ | RAG orchestration | Chains retrieval + LLM together; handles prompt templates and document splitting |
| PyAudio | 0.2.14+ | Microphone capture | Low-level audio input from system microphone |
| sounddevice | 0.5+ | Audio playback | Playing TTS output through speakers |
| PySide6 / PyQt6 | 6.7+ | Kiosk UI | Full-screen kiosk display with transcript and visuals |
| langchain-community | 0.3+ | Document loaders | Loading PDFs, markdown, text files into RAG pipeline |
| unstructured | 0.16+ | Document parsing | Extracting text from diverse document formats for knowledge base |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Python package management | Faster than pip, handles virtual environments |
| pytest | Testing | Test RAG retrieval accuracy, pipeline integration |
| nvidia-smi | GPU monitoring | Monitor VRAM usage during development |

## VRAM Budget

| Component | Model | VRAM Usage | Notes |
|-----------|-------|------------|-------|
| STT | faster-whisper medium | ~2GB | Loaded on demand, unloaded after transcription |
| LLM | Llama 3.1 8B Q4_K_M | ~5GB | Kept loaded via Ollama (primary resident) |
| TTS | Piper (ONNX) | ~0GB GPU | Runs on CPU, no VRAM needed |
| Embeddings | all-MiniLM-L6-v2 | ~0.1GB | Tiny, can stay loaded |
| **Total (concurrent)** | | **~7GB** | Well within 24GB budget |
| **Total (peak)** | | **~7GB** | STT + LLM + embeddings during query |

**Note:** With only ~7GB VRAM needed, there's headroom to upgrade to larger models later (e.g., Llama 3.1 70B Q4 at ~40GB wouldn't fit, but Mistral 7B or Phi-3 Medium 14B at ~9GB would).

## Installation

```bash
# Create project
uv init icl-voice-assistant
cd icl-voice-assistant

# Core dependencies
uv add faster-whisper ollama chromadb sentence-transformers langchain langchain-community

# Audio
uv add pyaudio sounddevice

# UI
uv add PySide6

# TTS
uv add piper-tts

# Document processing
uv add unstructured python-magic-bin

# Dev dependencies
uv add --dev pytest pytest-asyncio
```

```bash
# Install Ollama separately (system-level)
# Windows: Download from https://ollama.com/download
ollama pull llama3.1:8b-instruct-q4_K_M
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Faster Whisper | OpenAI Whisper | If you need word-level timestamps or don't care about speed |
| Faster Whisper | Whisper.cpp | If you want C++ performance and don't need Python integration |
| Ollama | llama.cpp / vLLM | If you need more control over inference parameters or batching |
| Piper TTS | Coqui TTS (XTTS) | If you need voice cloning or higher quality (but uses GPU VRAM) |
| Piper TTS | StyleTTS2 | If you want state-of-the-art quality and have VRAM budget |
| ChromaDB | FAISS | If you need faster similarity search at scale (>100k docs) |
| ChromaDB | Qdrant | If you need filtering, multi-tenancy, or production features |
| PySide6 | Electron + React | If you want web-based UI (heavier, but more flexible styling) |
| LangChain | LlamaIndex | If RAG is the primary focus and you want more retrieval options |
| Llama 3.1 8B | Mistral 7B v0.3 | Similar quality, slightly different strengths — good alternative |
| Llama 3.1 8B | Phi-3 Medium 14B | Better quality if VRAM allows (~9GB Q4) |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| OpenAI Whisper (original) | 4x slower than faster-whisper, same accuracy | faster-whisper |
| Full-precision LLM models | Won't fit in 24GB VRAM for useful sizes | Q4/Q5 quantized via Ollama |
| Google TTS / Amazon Polly | Cloud APIs — violates local-only constraint | Piper TTS |
| Pinecone / Weaviate | Cloud vector DBs — violates local-only constraint | ChromaDB |
| gTTS | Requires internet (Google Translate API) | Piper TTS |
| Large embedding models (1B+) | Overkill for small knowledge base, wastes VRAM | all-MiniLM-L6-v2 |
| Tkinter | Dated UI toolkit, poor for modern kiosk UIs | PySide6 |

## Stack Patterns by Variant

**If VRAM is tight (16GB GPU):**
- Use faster-whisper small instead of medium
- Use Phi-3 Mini 3.8B instead of Llama 8B
- Keep Piper on CPU (already the default)

**If VRAM is plentiful (48GB+):**
- Use faster-whisper large-v3 for best accuracy
- Use Llama 3.1 70B Q4 for significantly better answers
- Consider Coqui XTTS for more natural TTS voice

**If latency is critical:**
- Use faster-whisper small (faster transcription, slightly less accurate)
- Enable Ollama's streaming response
- Use Piper's fastest voice model

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| faster-whisper 1.1+ | CUDA 12.x, cuDNN 9.x | Requires CTranslate2 with CUDA support |
| Ollama 0.5+ | CUDA 12.x | Auto-detects GPU |
| PySide6 6.7+ | Python 3.9-3.12 | Qt6 bindings |
| ChromaDB 0.5+ | Python 3.9+ | Uses SQLite internally |

## Sources

- Faster Whisper GitHub — performance benchmarks vs OpenAI Whisper
- Ollama documentation — model management and API
- Piper TTS GitHub — voice models and performance
- ChromaDB documentation — embedding and retrieval
- NVIDIA documentation — VRAM requirements for consumer GPUs

---
*Stack research for: Local AI Voice Assistant with RAG*
*Researched: 2026-01-30*
