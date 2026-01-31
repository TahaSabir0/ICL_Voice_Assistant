# Requirements: ICL Voice Assistant

**Defined:** 2026-01-30
**Core Value:** Students can ask about any ICL tool or piece of equipment and get accurate, useful guidance instantly.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Voice Interaction

- [ ] **VOICE-01**: User can press a button on screen to start speaking their question
- [ ] **VOICE-02**: System transcribes spoken audio to text using a local STT model with >90% accuracy
- [ ] **VOICE-03**: System speaks the generated answer aloud using a local TTS model

### Knowledge & Answers

- [ ] **KB-01**: System answers questions about ICL tools and equipment by retrieving relevant information from a RAG knowledge base
- [ ] **KB-02**: System includes safety information when answering questions about equipment that has safety considerations (laser cutter, CNC, etc.)
- [ ] **KB-03**: System responds with "I don't know" or directs to lab staff when the knowledge base lacks relevant information, rather than hallucinating

### Display

- [ ] **UI-01**: Screen displays the conversation transcript showing the user's question and the assistant's answer
- [ ] **UI-02**: Screen shows the current processing state (idle, listening, thinking, speaking)

### Knowledge Base Management

- [ ] **KBM-01**: Developer can add, edit, and remove knowledge base entries as markdown files, with changes reflected after re-ingestion

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Voice Interaction

- **VOICE-04**: User can ask follow-up questions within the same session with conversation context maintained
- **VOICE-05**: System streams TTS output to start speaking before the full answer is generated

### Knowledge & Answers

- **KB-04**: System recommends which tools to use when a student describes a project they want to build
- **KB-05**: Knowledge base includes images and diagrams that display alongside spoken answers

### Display

- **UI-03**: Screen shows relevant equipment photos or diagrams alongside the text answer
- **UI-04**: Screen shows an idle/attract display with example questions and lab information when not in use

### Knowledge Base Management

- **KBM-02**: Automated ingestion script rebuilds vector database from markdown files with a single command
- **KBM-03**: Knowledge base files tracked in git for version history

### Analytics

- **ANLY-01**: System logs what students ask about most for lab improvement insights

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Event scheduling / calendar | Deferred — not core to tool guidance mission |
| Cloud AI APIs | Must be fully local — privacy, reliability, no ongoing costs |
| Wake word activation | Push-to-talk is simpler and avoids always-on listening concerns |
| User accounts / login | Kiosk is anonymous — no authentication needed |
| Conversation history across sessions | Each interaction is standalone |
| Multilingual support | English-only for v1 — multiplies STT/TTS complexity |
| Real-time equipment status | Would require IoT sensors — out of scope |
| Booking / reservations | Separate system — assistant can direct students to it |
| Mobile / web remote access | Kiosk-only deployment for v1 |
| Admin dashboard | Developer edits files directly for v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| VOICE-01 | — | Pending |
| VOICE-02 | — | Pending |
| VOICE-03 | — | Pending |
| KB-01 | — | Pending |
| KB-02 | — | Pending |
| KB-03 | — | Pending |
| UI-01 | — | Pending |
| UI-02 | — | Pending |
| KBM-01 | — | Pending |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 0
- Unmapped: 9

---
*Requirements defined: 2026-01-30*
*Last updated: 2026-01-30 after initial definition*
