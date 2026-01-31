# Roadmap: ICL Voice Assistant

## Overview

Build a locally hosted voice assistant for the ICL in 3 phases: first get the core voice pipeline working (STT → LLM → TTS), then add the knowledge base and RAG so it can answer real questions about lab tools, then build the kiosk UI and integrate everything for deployment. Each phase delivers something testable — Phase 1 proves the hardware works, Phase 2 proves the assistant gives useful answers, Phase 3 makes it ready for students.

## Phases

- [ ] **Phase 1: Voice Pipeline** - Local STT, LLM, and TTS working end-to-end on the server
- [ ] **Phase 2: Knowledge Base & RAG** - ICL knowledge base with retrieval-augmented answers
- [ ] **Phase 3: Kiosk UI & Integration** - Full-screen kiosk display with push-to-talk, deployed and stable

## Phase Details

### Phase 1: Voice Pipeline
**Goal**: Get the core voice pipeline working — record audio, transcribe with Faster Whisper, generate an answer with Ollama/Llama 3.1, speak it back with Piper TTS. Validate VRAM budget and end-to-end latency on the actual hardware.
**Depends on**: Nothing (first phase)
**Requirements**: VOICE-01, VOICE-02, VOICE-03
**Success Criteria** (what must be TRUE):
  1. User can record audio via microphone by pressing a key and the system transcribes it to text
  2. System generates a spoken answer using a local LLM and TTS — audio plays through speakers
  3. End-to-end latency from speech end to audio response start is under 8 seconds
  4. All models (STT + LLM + TTS) run on the local GPU/CPU without errors
**Plans**: 3 plans

Plans:
- [ ] 01-01: Set up project, install dependencies, configure Ollama with Llama 3.1
- [ ] 01-02: Implement audio capture + Faster Whisper STT + Piper TTS
- [ ] 01-03: Wire the full pipeline (audio → STT → LLM → TTS → playback) and benchmark

### Phase 2: Knowledge Base & RAG
**Goal**: Build the ICL knowledge base as markdown files, set up document ingestion into ChromaDB, and integrate RAG retrieval into the LLM pipeline so the assistant answers questions accurately about lab tools with safety information.
**Depends on**: Phase 1
**Requirements**: KB-01, KB-02, KB-03, KBM-01
**Success Criteria** (what must be TRUE):
  1. Knowledge base contains documentation for all major ICL tools (3D printers, laser cutters, CNC, vinyl cutters, sewing/embroidery, sublimation, VR)
  2. When asked about a specific tool, the system retrieves relevant knowledge base content and generates an accurate answer
  3. When asked about a tool with safety considerations, the response includes safety information
  4. When asked about something not in the knowledge base, the system admits it doesn't know rather than hallucinating
  5. Developer can edit markdown files and re-ingest to update what the assistant knows
**Plans**: 3 plans

Plans:
- [ ] 02-01: Create knowledge base structure and write initial tool documentation
- [ ] 02-02: Build document ingestion pipeline (markdown → chunks → embeddings → ChromaDB)
- [ ] 02-03: Integrate RAG retrieval into LLM pipeline with system prompt engineering

### Phase 3: Kiosk UI & Integration
**Goal**: Build the full-screen PySide6 kiosk interface with push-to-talk button, conversation transcript, and processing state indicators. Integrate all pipeline components into the UI and validate stability for continuous operation.
**Depends on**: Phase 2
**Requirements**: UI-01, UI-02
**Success Criteria** (what must be TRUE):
  1. Application launches in full-screen kiosk mode showing an idle state
  2. User can press an on-screen button to start recording, and the UI shows a "listening" state
  3. After speaking, the UI shows "thinking" state, then displays both the question and answer as text
  4. The answer is spoken aloud through speakers while displayed on screen
  5. Application runs stably for 24 hours of continuous operation without crashes or memory leaks
**Plans**: 3 plans

Plans:
- [ ] 03-01: Build PySide6 kiosk window with push-to-talk button and state indicators
- [ ] 03-02: Integrate voice pipeline and RAG into the UI with threaded processing
- [ ] 03-03: Stability testing, error handling, and auto-restart configuration

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Voice Pipeline | 0/3 | Not started | - |
| 2. Knowledge Base & RAG | 0/3 | Not started | - |
| 3. Kiosk UI & Integration | 0/3 | Not started | - |
