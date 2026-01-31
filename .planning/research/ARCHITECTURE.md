# Architecture Research

**Domain:** Local AI Voice Assistant with RAG
**Researched:** 2026-01-30
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         KIOSK UI (PySide6)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Push-to-Talk │  │  Transcript  │  │   Visual Content     │   │
│  │    Button    │  │   Display    │  │   (images/diagrams)  │   │
│  └──────┬───────┘  └──────▲───────┘  └──────────▲───────────┘   │
│         │                 │                     │               │
├─────────┼─────────────────┼─────────────────────┼───────────────┤
│         │          VOICE PIPELINE                │               │
│         ▼                 │                     │               │
│  ┌──────────────┐         │                     │               │
│  │ Audio Capture │         │                     │               │
│  │  (PyAudio)   │         │                     │               │
│  └──────┬───────┘         │                     │               │
│         ▼                 │                     │               │
│  ┌──────────────┐         │                     │               │
│  │     STT      │         │                     │               │
│  │(Faster       │         │                     │               │
│  │ Whisper)     │         │                     │               │
│  └──────┬───────┘         │                     │               │
│         ▼                 │                     │               │
│  ┌──────────────┐  ┌──────┴───────┐             │               │
│  │  RAG Engine  │──│  LLM (Ollama)│─────────────┘               │
│  │ (LangChain + │  │  Llama 3.1   │                             │
│  │  ChromaDB)   │  └──────┬───────┘                             │
│  └──────────────┘         ▼                                     │
│                    ┌──────────────┐                              │
│                    │     TTS      │                              │
│                    │ (Piper TTS)  │──▶ Speaker Output            │
│                    └──────────────┘                              │
├─────────────────────────────────────────────────────────────────┤
│                      KNOWLEDGE BASE                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Documents    │  │  ChromaDB    │  │  Image Assets        │   │
│  │ (markdown/   │  │  (vectors)   │  │  (tool photos,       │   │
│  │  PDF/text)   │  │              │  │   diagrams)          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Kiosk UI | Full-screen display, push-to-talk button, transcript, visuals | PySide6 QMainWindow with QML or widgets |
| Audio Capture | Record microphone input when push-to-talk active | PyAudio stream with silence detection for end-of-speech |
| STT Engine | Convert audio buffer to text | faster-whisper with CTranslate2 backend on GPU |
| RAG Engine | Retrieve relevant knowledge base chunks for a query | LangChain RetrievalQA with ChromaDB vector store |
| LLM Service | Generate natural language answers from retrieved context | Ollama serving Llama 3.1 8B, accessed via HTTP API |
| TTS Engine | Convert answer text to audio | Piper TTS on CPU, outputs WAV buffer |
| Audio Playback | Play TTS audio through speakers | sounddevice or PyAudio output stream |
| Knowledge Base | Store and index makerspace tool documentation | Markdown files → chunked → embedded → ChromaDB |
| KB Ingestion | Process documents into vector embeddings | LangChain document loaders + text splitters + embeddings |

## Recommended Project Structure

```
icl-voice-assistant/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── app.py                  # Application orchestrator
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── capture.py          # Microphone recording + silence detection
│   │   └── playback.py         # Speaker audio output
│   ├── stt/
│   │   ├── __init__.py
│   │   └── whisper.py          # Faster Whisper STT engine
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── ollama.py           # Ollama LLM client
│   │   └── prompts.py          # System prompts and templates
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py        # ChromaDB retrieval logic
│   │   ├── embeddings.py       # Embedding model wrapper
│   │   └── ingest.py           # Document ingestion pipeline
│   ├── tts/
│   │   ├── __init__.py
│   │   └── piper.py            # Piper TTS engine
│   └── ui/
│       ├── __init__.py
│       ├── kiosk.py            # Main kiosk window
│       ├── widgets/
│       │   ├── __init__.py
│       │   ├── talk_button.py  # Push-to-talk button widget
│       │   ├── transcript.py   # Conversation transcript display
│       │   └── visual.py       # Image/diagram display area
│       └── styles/
│           └── kiosk.qss       # Qt stylesheet for kiosk appearance
├── knowledge_base/
│   ├── tools/                  # Tool documentation (markdown)
│   │   ├── 3d-printing.md
│   │   ├── laser-cutting.md
│   │   ├── cnc.md
│   │   └── ...
│   ├── images/                 # Equipment photos and diagrams
│   └── ingest.py               # Script to rebuild vector DB
├── data/
│   └── chroma/                 # ChromaDB persistent storage
├── tests/
│   ├── test_stt.py
│   ├── test_rag.py
│   ├── test_tts.py
│   └── test_pipeline.py
├── pyproject.toml
└── README.md
```

### Structure Rationale

- **src/ with domain folders:** Each AI component (stt, llm, rag, tts) is isolated — can be developed and tested independently
- **knowledge_base/:** Separate from code — developer edits markdown files here to update what the assistant knows
- **data/chroma/:** Persistent vector DB storage, rebuilt from knowledge_base/ when content changes
- **ui/ with widgets/:** Kiosk UI components separated for maintainability

## Architectural Patterns

### Pattern 1: Pipeline Architecture

**What:** Each voice interaction flows through a sequential pipeline: Audio → STT → RAG → LLM → TTS → Audio Out
**When to use:** Always — this is the core interaction pattern
**Trade-offs:** Simple to understand and debug. Latency is sum of all stages. Can't parallelize dependent stages, but UI updates can happen in parallel with processing.

### Pattern 2: Event-Driven UI Updates

**What:** Pipeline stages emit events (transcription_ready, retrieval_complete, answer_ready, audio_ready) that the UI subscribes to
**When to use:** For updating the screen as the pipeline processes — show transcription immediately, then show answer as it streams
**Trade-offs:** More responsive UX. Slightly more complex wiring. Qt signals/slots are a natural fit.

### Pattern 3: Async Pipeline with Threading

**What:** Audio capture on dedicated thread, AI pipeline on main/worker thread, UI on Qt main thread
**When to use:** Always — audio capture must not block UI, and AI inference must not freeze the display
**Trade-offs:** Need thread safety. Qt's signal/slot mechanism handles cross-thread communication cleanly.

## Data Flow

### Request Flow

```
[Student presses button]
    ↓
[Audio Capture] → records until button released or silence detected
    ↓
[WAV buffer]
    ↓
[STT (Faster Whisper)] → transcribes audio to text
    ↓                      ↓ (emit: transcription_ready → UI shows question)
[Query text]
    ↓
[RAG Retriever] → embeds query → searches ChromaDB → returns top-k chunks
    ↓
[Context + Query]
    ↓
[LLM (Ollama)] → generates answer using context + system prompt
    ↓               ↓ (emit: answer_ready → UI shows answer text + images)
[Answer text]
    ↓
[TTS (Piper)] → synthesizes speech from answer text
    ↓
[Audio buffer]
    ↓
[Audio Playback] → plays through speakers
```

### State Management

```
[AppState]
├── is_recording: bool          # Push-to-talk active
├── is_processing: bool         # Pipeline running
├── current_transcript: str     # User's transcribed question
├── current_answer: str         # LLM's response
├── current_visuals: list       # Images/diagrams to display
└── ui_state: enum              # IDLE | LISTENING | PROCESSING | SPEAKING
```

State is simple — no persistence needed across interactions. Each push-to-talk starts fresh.

### Key Data Flows

1. **Voice-to-answer flow:** Mic → WAV → text → vector search → context → LLM → answer text → speech → speaker (linear pipeline)
2. **Knowledge ingestion flow:** Markdown files → text splitter → embeddings → ChromaDB (batch, run on demand)
3. **UI update flow:** Pipeline events → Qt signals → widget updates (parallel to main pipeline)

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single kiosk (v1) | Monolith is perfect — everything on one machine |
| Multiple kiosks | Separate Ollama server from kiosk clients; kiosks become thin clients |
| Large knowledge base (>1000 docs) | Tune chunk size, consider hybrid search (keyword + vector) |

### Scaling Priorities

1. **First bottleneck:** Pipeline latency — STT + LLM + TTS adds up. Optimize with model selection, streaming TTS, and keeping models loaded
2. **Second bottleneck:** Knowledge base quality — as KB grows, retrieval precision drops. Tune chunk size and add metadata filtering

## Anti-Patterns

### Anti-Pattern 1: Loading Models Per Request

**What people do:** Load STT/LLM/TTS models fresh for each question
**Why it's wrong:** Model loading takes 5-30 seconds, creating unacceptable latency
**Do this instead:** Load models at application startup, keep them resident in memory

### Anti-Pattern 2: Giant Documents in RAG

**What people do:** Put entire manuals as single documents in the vector store
**Why it's wrong:** Retrieval returns irrelevant sections, LLM context window wasted
**Do this instead:** Chunk documents into 200-500 token pieces with overlap, add metadata (tool name, category)

### Anti-Pattern 3: No Silence Detection

**What people do:** Record audio for a fixed duration (e.g., always 10 seconds)
**Why it's wrong:** Either cuts off long questions or adds unnecessary silence/delay
**Do this instead:** Detect silence after speech to auto-stop recording (with timeout fallback)

### Anti-Pattern 4: Synchronous Pipeline Blocking UI

**What people do:** Run the entire AI pipeline on the UI thread
**Why it's wrong:** UI freezes, no progress indication, feels broken
**Do this instead:** Run pipeline in worker thread, emit Qt signals for UI updates

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| UI ↔ Audio | Qt signals + shared buffer | Audio capture emits signal when recording complete |
| Audio ↔ STT | WAV buffer passed directly | In-process, same Python runtime |
| STT ↔ RAG | Text string | Simple function call |
| RAG ↔ LLM | Prompt string (context + query) | HTTP to Ollama localhost API |
| LLM ↔ TTS | Text string | In-process call to Piper |
| TTS ↔ Audio Playback | WAV buffer | Direct playback via sounddevice |
| Knowledge Base ↔ RAG | ChromaDB queries | Persistent embedded DB, queried at runtime |

### External Services

None — fully local. Ollama runs as a local service on localhost.

## Sources

- Local LLM deployment patterns and Ollama architecture
- RAG pipeline design with LangChain and vector databases
- Qt/PySide6 application architecture for kiosk deployments
- Voice assistant pipeline design patterns

---
*Architecture research for: Local AI Voice Assistant with RAG*
*Researched: 2026-01-30*
