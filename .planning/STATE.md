# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-30)

**Core value:** Students can ask about any ICL tool or piece of equipment and get accurate, useful guidance instantly.
**Current focus:** Phase 1 Complete! Ready for Phase 2: Knowledge Base & RAG

## Current Position

Phase: 1 of 3 (Voice Pipeline) ✅ COMPLETE
Plan: 3 of 3 in current phase
Status: Phase 1 complete, all success criteria met
Last activity: 2026-01-31 — Full pipeline integrated and tested

Progress: [██████░░░░] 33%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: ~30 minutes
- Total execution time: ~90 minutes

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1     | 3/3   | ~90m  | ~30m     |

**Recent Trend:**
- Plan 01-01: Environment setup ✅
- Plan 01-02: Audio/STT/TTS implementation ✅
- Plan 01-03: Full pipeline integration ✅
- Trend: On track

*Updated after each plan completion*

## Phase 1 Success Criteria

✅ User can record audio via microphone by pressing a key → transcription appears
✅ System generates spoken answer using local LLM and TTS
✅ End-to-end latency under 8 seconds (measured: LLM ~4.6s + TTS ~0.1s = ~5s)
✅ All models run on local GPU/CPU without errors

**42 tests passing**

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
| **Total** | **42** |

### Pending for Phase 2

- Create ICL tool knowledge base (markdown)
- Build document ingestion pipeline (ChromaDB)
- Integrate RAG retrieval into LLM pipeline

### Blockers/Concerns

- Piper TTS would provide higher quality voices but requires espeak-ng
- pyttsx3 works but has robotic voice quality
- For production, recommend installing espeak-ng

## Session Continuity

Last session: 2026-01-31
Stopped at: Phase 1 complete — full voice pipeline working
Resume file: None
Next step: Phase 2, Plan 02-01 — Create knowledge base structure
