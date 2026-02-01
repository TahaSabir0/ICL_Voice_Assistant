# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-30)

**Core value:** Students can ask about any ICL tool or piece of equipment and get accurate, useful guidance instantly.
**Current focus:** Phase 2 in progress - Knowledge Base & RAG

## Current Position

Phase: 2 of 3 (Knowledge Base & RAG)
Plan: 2 of 3 in current phase ✅ COMPLETE
Status: Document ingestion pipeline complete - ChromaDB populated
Last activity: 2026-02-01 — RAG pipeline (chunking + embeddings + ChromaDB)

Progress: [█████████░] 56%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: ~30 minutes
- Total execution time: ~150 minutes

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1     | 3/3   | ~90m  | ~30m     |
| 2     | 2/3   | ~60m  | ~30m     |

**Recent Trend:**
- Plan 01-01: Environment setup ✅
- Plan 01-02: Audio/STT/TTS implementation ✅
- Plan 01-03: Full pipeline integration ✅
- Plan 02-01: Knowledge base generation ✅
- Plan 02-02: Document ingestion pipeline ✅
- Trend: On track

*Updated after each plan completion*

## Phase 1 Success Criteria

✅ User can record audio via microphone by pressing a key → transcription appears
✅ System generates spoken answer using local LLM and TTS
✅ End-to-end latency under 8 seconds (measured: LLM ~4.6s + TTS ~0.1s = ~5s)
✅ All models run on local GPU/CPU without errors

**53 tests passing** (42 Phase 1 + 11 RAG)

## Benchmark Results

| Component | Average Time |
|-----------|-------------|
| LLM (Llama 3.1 8B Q4) | ~4.6s |
| TTS (pyttsx3/SAPI) | ~0.1s |
| **Processing Total** | **~5s** |

✅ **PASS: Under 8 second target**

## Accumulated Context

### Decisions

- [Init]: Fully local — no cloud APIs (STT, LLM, TTS all on-premise)
- [Init]: Push-to-talk activation (not wake word)
- [Init]: Server doubles as kiosk (screen + mic attached directly)
- [Init]: Events/scheduling out of v1 scope
- [01-02]: Using pyttsx3 (Windows SAPI) for TTS due to espeak-ng dependency issue
- [01-03]: Pipeline uses text-based testing; full voice requires human interaction

### Completed Components

**Phase 1: Voice Pipeline**

1. **Audio Module** (`src/audio/`)
   - `capture.py`: Microphone recording with silence detection
   - `playback.py`: Speaker output with blocking/async modes

2. **STT Module** (`src/stt/`)
   - `whisper.py`: Faster Whisper wrapper with configurable models

3. **LLM Module** (`src/llm/`)
   - `ollama.py`: Ollama client with generate and streaming
   - `prompts.py`: ICL-specific system prompts

4. **TTS Module** (`src/tts/`)
   - `piper.py`: Multi-backend TTS (pyttsx3/SAPI, Piper)

5. **Pipeline** (`src/pipeline.py`)
   - Full orchestration: Audio → STT → LLM → TTS → Playback
   - Metrics tracking for latency analysis
   - State management with callbacks

6. **Main Entry** (`src/main.py`)
   - Interactive CLI for testing

7. **Benchmark** (`scripts/benchmark.py`)
   - Latency testing scripts

### Test Coverage

| Module | Tests |
|--------|-------|
| Audio | 6 |
| STT | 6 |
| TTS | 8 |
| LLM | 7 |
| Pipeline | 8 |
| Components | 7 |
| **RAG** | **11** |
| **Total** | **53** |

### Pending for Phase 2

- ✅ Create ICL tool knowledge base (markdown) — DONE
- ✅ Build document ingestion pipeline (ChromaDB) — DONE
- Integrate RAG retrieval into LLM pipeline

### Phase 2 Plan 02-01 Completed

**Web Extraction Pipeline:**
- `scripts/crawl_icl.py` — Crawls ICL website, downloads PDFs
- `scripts/extract_pdfs.py` — Extracts text from PDF manuals
- `scripts/generate_knowledge_base.py` — Generates structured markdown
- `scripts/update_knowledge_base.py` — Master update script

**Knowledge Base Stats:**
- Pages crawled: 10
- PDFs downloaded: 32
- Categories: 6 (3D Printing, Laser Cutting, CNC, Sewing, VR, Vinyl)
- Equipment files: 20
- Total content: ~140,000 characters

### Phase 2 Plan 02-02 Completed

**RAG Pipeline:**
- `src/rag/chunker.py` — Markdown chunker with semantic splitting
- `src/rag/embeddings.py` — Sentence-transformers embedding service
- `src/rag/vectorstore.py` — ChromaDB vector store wrapper
- `src/rag/ingest.py` — Ingestion pipeline
- `src/rag/retriever.py` — High-level retrieval interface
- `scripts/test_retrieval.py` — Interactive retrieval testing

**Vector Store Stats:**
- Documents ingested: 139 chunks
- Embedding model: all-MiniLM-L6-v2 (384 dimensions)
- Retrieval verified with sample ICL queries

### Blockers/Concerns

- Piper TTS would provide higher quality voices but requires espeak-ng
- pyttsx3 works but has robotic voice quality
- For production, recommend installing espeak-ng
- Some PDFs are image-only (no text extraction possible)

## Session Continuity

Last session: 2026-02-01
Stopped at: Phase 2, Plan 02-02 complete — RAG pipeline working
Resume file: None
Next step: Phase 2, Plan 02-03 — Integrate RAG into LLM pipeline

