# Project Research Summary

**Project:** ICL Voice Assistant
**Domain:** Local AI Voice Assistant with RAG for Makerspace
**Researched:** 2026-01-30
**Confidence:** HIGH

## Executive Summary

Building a locally hosted voice assistant with RAG is a well-understood pattern in 2025. The Python ML ecosystem provides mature, production-ready components for every stage of the pipeline: Faster Whisper for STT, Ollama + Llama 3.1 for LLM inference, Piper for TTS, and ChromaDB + LangChain for RAG. The total VRAM budget (~7GB) fits comfortably within the 24GB consumer GPU constraint, leaving headroom for model upgrades.

The recommended approach is a sequential pipeline architecture: Audio → STT → RAG → LLM → TTS → Audio Out, with event-driven UI updates running in parallel. PySide6 provides the kiosk display. The knowledge base is maintained as simple markdown files that get chunked and embedded into ChromaDB, with a simple script to rebuild the vector store when content changes.

Key risks are pipeline latency (must stay under 5 seconds end-to-end), RAG retrieval quality (wrong chunks = wrong answers), and long-running stability (24/7 unattended operation). All are manageable with the right model choices and testing discipline.

## Key Findings

### Recommended Stack

Python 3.11+ with a focused set of ML libraries. The key insight is that VRAM usage is very manageable — Piper TTS runs on CPU, and the quantized LLM + STT + embeddings together only use ~7GB VRAM.

**Core technologies:**
- **Faster Whisper** (STT): 4x faster than original Whisper, ~2GB VRAM, excellent accuracy
- **Ollama + Llama 3.1 8B Q4_K_M** (LLM): Simple model management, ~5GB VRAM, strong instruction following
- **Piper TTS** (text-to-speech): Runs on CPU, fast, natural voices, zero VRAM
- **ChromaDB + LangChain** (RAG): Embedded vector DB, no server needed, mature retrieval pipeline
- **PySide6** (UI): Qt-based kiosk display with full-screen support

### Expected Features

**Must have (table stakes):**
- Voice input with push-to-talk
- Spoken response with on-screen transcript
- Tool/equipment Q&A (core use case)
- Responsive latency (<5 seconds)
- Graceful "I don't know" (no hallucination)

**Should have (competitive):**
- Safety warnings for equipment
- Project-to-tool recommendations
- Step-by-step guidance with images
- Idle/attract screen

**Defer (v2+):**
- Multi-turn follow-up conversations
- Multilingual support
- Usage analytics

### Architecture Approach

A monolithic Python application running on a single machine, organized as a sequential voice pipeline with event-driven UI updates. Audio capture runs on a dedicated thread, the AI pipeline runs on worker threads, and the Qt UI runs on the main thread. The knowledge base is stored as markdown files in a git-tracked directory, with ChromaDB providing vector search at runtime.

**Major components:**
1. **Kiosk UI** (PySide6) — full-screen display with push-to-talk, transcript, visuals
2. **Voice Pipeline** — Audio Capture → STT → RAG → LLM → TTS → Playback
3. **Knowledge Base** — Markdown files → chunked → embedded → ChromaDB

### Critical Pitfalls

1. **VRAM exhaustion** — Budget carefully, keep models loaded, use Ollama for management
2. **Pipeline latency >5s** — Use faster-whisper, quantized LLM, CPU-based TTS, benchmark each stage
3. **Poor RAG retrieval** — Chunk documents properly (200-500 tokens), add metadata, test with real questions
4. **Hallucinated safety info** — System prompt must refuse safety advice not in KB, direct to staff
5. **Mic noise in makerspace** — Use directional mic, apply VAD, test with real lab noise

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation & Voice Pipeline
**Rationale:** Core pipeline must work before anything else — validates hardware, VRAM budget, and latency assumptions
**Delivers:** Working STT → LLM → TTS pipeline (without RAG — just direct question answering)
**Addresses:** Voice input, spoken response, push-to-talk, basic UI
**Avoids:** VRAM exhaustion pitfall (validated early), latency pitfall (measured from start)

### Phase 2: Knowledge Base & RAG
**Rationale:** RAG is what makes this useful for the ICL — without domain knowledge it's just a generic chatbot
**Delivers:** Knowledge base structure, document ingestion, vector retrieval, RAG-enhanced answers
**Addresses:** Tool Q&A, accurate domain-specific answers, "I don't know" handling
**Avoids:** RAG quality pitfall (tested in isolation), safety hallucination pitfall (safety docs in KB)

### Phase 3: Kiosk UI & Polish
**Rationale:** Once the pipeline works with RAG, polish the visual experience for students
**Delivers:** Full-screen kiosk UI, transcript display, visual content, idle screen, stability
**Addresses:** On-screen transcript, visuals, project recommendations, deployment readiness
**Avoids:** UX pitfalls (readable at distance, processing feedback), stability pitfall (24h testing)

### Phase Ordering Rationale

- Phase 1 first because it validates hardware feasibility and core pipeline
- Phase 2 second because RAG quality needs testing before UI polish
- Phase 3 last because UI can be rough while validating the AI pipeline works

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Audio capture and noise handling — may need mic hardware testing
- **Phase 2:** RAG chunking strategy — depends on actual knowledge base content

Phases with standard patterns (skip research-phase):
- **Phase 3:** PySide6 kiosk patterns — well-documented, established approaches

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All components are mature, well-documented, widely used |
| Features | HIGH | Clear requirements from questioning, domain is well-understood |
| Architecture | HIGH | Pipeline architecture is standard for voice assistants |
| Pitfalls | HIGH | Common failure modes well-documented in community |

**Overall confidence:** HIGH

### Gaps to Address

- Actual mic hardware selection and testing in the lab environment
- Exact knowledge base content structure (depends on what documentation exists)
- LLM system prompt tuning (needs iteration with real questions)

## Sources

### Primary (HIGH confidence)
- Faster Whisper documentation and benchmarks
- Ollama documentation and model library
- ChromaDB and LangChain documentation
- PySide6/Qt documentation

### Secondary (MEDIUM confidence)
- Community benchmarks for local LLM inference performance
- Voice assistant UX design guidelines
- Makerspace kiosk deployment patterns

---
*Research completed: 2026-01-30*
*Ready for roadmap: yes*
