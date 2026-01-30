# ICL Voice Assistant

## What This Is

A locally hosted AI voice assistant for the Innovation & Creativity Lab (ICL) at Gettysburg College. Students walk up to a kiosk (server with attached screen and microphone), press a button, and ask questions about lab tools and equipment. The assistant processes speech locally, retrieves answers from a knowledge base about the ICL, and responds with spoken audio and an on-screen transcript with visuals. All processing — speech-to-text, LLM inference, and text-to-speech — runs on-premise with no cloud dependencies.

## Core Value

Students can ask about any ICL tool or piece of equipment and get accurate, useful guidance instantly.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Local speech-to-text converts student voice input to text
- [ ] Local LLM generates answers using RAG over ICL knowledge base
- [ ] Local text-to-speech speaks the answer back to the student
- [ ] Push-to-talk button activates listening
- [ ] Screen displays conversation transcript and relevant visuals
- [ ] Knowledge base covers all ICL tools and equipment with usage guidance
- [ ] Knowledge base can be updated by a developer (add/edit/remove entries)
- [ ] Project recommendation capability — suggest which tools to use for a given project idea

### Out of Scope

- Event scheduling and calendar integration — deferred, not needed for v1
- Cloud API integration — system must be fully local and offline-capable
- Wake word activation — push-to-talk is sufficient for v1
- Conversation memory across sessions — each interaction is standalone
- Custom assistant personality — not a priority
- Mobile/web remote access — kiosk-only for v1

## Context

The Innovation & Creativity Lab (ICL) at Gettysburg College is a makerspace on the first floor of Plank Gym, open 24/7 to students, faculty, and staff. Equipment includes:

- **Digital fabrication:** 3D printers, laser cutters, CNC machining, vinyl cutters
- **Textiles:** Sewing machines, embroidery machines, sublimation printing
- **Digital exploration:** Virtual reality systems, AI Media Lab
- **Planned expansions:** Audio and video recording studios

The knowledge base is currently a mix of existing documentation (PDFs, guides, website content) and undocumented tribal knowledge held by lab staff. Part of this project involves consolidating that information into a structured, queryable format.

The assistant serves as a first point of contact — students who don't know where to start can ask the assistant which tools exist, how to use them, and which ones are right for their project.

## Constraints

- **Hardware:** Single server with consumer NVIDIA GPU (~24GB VRAM), screen and microphone attached directly — this machine is both the server and the kiosk
- **Network:** Must function fully offline with no cloud dependencies — all STT, LLM, and TTS run locally
- **VRAM budget:** ~24GB must accommodate STT model + LLM + TTS model (may need careful model selection or sequential loading)
- **Maintenance:** Knowledge base updates handled by a single developer (not non-technical staff)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fully local (no cloud) | Privacy, reliability, no ongoing API costs, works offline | — Pending |
| Push-to-talk (not wake word) | Simpler implementation, avoids always-on listening concerns | — Pending |
| Server doubles as kiosk | Available hardware, reduces complexity of separate kiosk device | — Pending |
| Events out of v1 scope | Focus on core tool guidance first | — Pending |

---
*Last updated: 2026-01-30 after initialization*
