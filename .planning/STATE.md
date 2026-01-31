# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-30)

**Core value:** Students can ask about any ICL tool or piece of equipment and get accurate, useful guidance instantly.
**Current focus:** Phase 1: Voice Pipeline

## Current Position

Phase: 1 of 3 (Voice Pipeline)
Plan: 2 of 3 in current phase
Status: Plan 01-02 complete, ready for 01-03
Last activity: 2026-01-31 — Implemented audio, STT, and TTS modules

Progress: [███░░░░░░░] 30%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: ~25 minutes
- Total execution time: ~50 minutes

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1     | 2/3   | ~50m  | ~25m     |

**Recent Trend:**
- Plan 01-01: Environment setup ✅
- Plan 01-02: Audio/STT/TTS implementation ✅
- Trend: On track

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Fully local — no cloud APIs (STT, LLM, TTS all on-premise)
- [Init]: Push-to-talk activation (not wake word)
- [Init]: Server doubles as kiosk (screen + mic attached directly)
- [Init]: Events/scheduling out of v1 scope
- [01-02]: Using pyttsx3 (Windows SAPI) for TTS instead of Piper due to espeak-ng dependency issue on Python 3.13
- [01-02]: Piper TTS available as optional backend when espeak-ng is installed

### Completed Components

**Plan 01-01: Environment Setup**
- Project structure created (src/, tests/, knowledge_base/, data/)
- pyproject.toml with all dependencies
- Virtual environment with 140+ packages installed
- Llama 3.1 8B Q4 model pulled via Ollama
- All 7 component verification tests passing

**Plan 01-02: Component Implementation**
- Audio capture module (src/audio/capture.py)
  - Silence detection, configurable thresholds
  - Threaded recording with callbacks
- Audio playback module (src/audio/playback.py)
  - Blocking and async playback
- STT module (src/stt/whisper.py)
  - Faster Whisper wrapper
  - Configurable model size and device
  - TranscriptionResult with segments and metadata
- TTS module (src/tts/piper.py)
  - Multi-backend support (pyttsx3/SAPI, Piper)
  - TTSResult with audio and timing info
- All 20 tests passing (6 audio + 6 STT + 8 TTS)

### Pending Todos

- Plan 01-03: Wire the full pipeline (audio → STT → LLM → TTS → playback)
- Benchmark end-to-end latency
- Verify <8 second response time target

### Blockers/Concerns

- Piper TTS requires espeak-ng to be installed (not available on Python 3.13 via pip)
- Using pyttsx3 as fallback, which has lower audio quality but works out of the box
- For production, recommend installing espeak-ng system package

## Session Continuity

Last session: 2026-01-31
Stopped at: Plan 01-02 complete — all component modules implemented and tested
Resume file: None
Next step: Plan 01-03 — Wire full pipeline and benchmark
