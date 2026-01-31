# Feature Research

**Domain:** Local AI Voice Assistant for Makerspace
**Researched:** 2026-01-30
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = assistant feels broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Voice input (STT) | It's a voice assistant — students expect to speak to it | HIGH | Needs good accuracy in noisy makerspace environment |
| Spoken response (TTS) | Students expect to hear the answer, not just read it | MEDIUM | Natural-sounding voice matters for engagement |
| Tool/equipment Q&A | Core purpose — "How do I use the laser cutter?" | MEDIUM | RAG retrieval + LLM generation |
| On-screen transcript | Students want to read along / reference after | LOW | Display what was said and the response |
| Responsive latency | Students expect conversational speed (<5s for answer) | HIGH | STT + retrieval + LLM + TTS pipeline latency |
| Push-to-talk | Clear interaction model — press to speak | LOW | Button on screen or physical |
| Graceful "I don't know" | Better to admit gaps than hallucinate wrong safety info | LOW | LLM prompt engineering |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Project-to-tool recommendation | "I want to build X" → suggests which tools/approach | MEDIUM | Requires richer knowledge base with project mappings |
| Step-by-step guidance with images | Show photos/diagrams of equipment alongside voice | MEDIUM | Knowledge base needs image references |
| Safety warnings for tools | Proactive safety info before using dangerous equipment | LOW | Critical for CNC, laser cutter — liability reduction |
| Follow-up questions | Multi-turn context — "What about the settings?" after laser cutter Q | MEDIUM | Conversation state management |
| Idle screen / attract mode | Shows lab info, tips, or branding when not in use | LOW | Encourages students to engage |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Always-on listening / wake word | "Hey ICL" feels futuristic | Privacy concerns, false activations in noisy lab, complex to implement well | Push-to-talk is reliable and clear |
| Booking/reservation system | "Reserve the 3D printer" | Requires integration with scheduling system, auth, state management | Display link/QR to existing booking system |
| User accounts / history | Remember past conversations | Privacy, complexity, students won't sign in at a kiosk | Each interaction is standalone |
| Real-time equipment status | "Is the laser cutter available?" | Requires IoT sensors on each machine, maintenance burden | Staff updates availability in knowledge base |
| Multilingual support | International students | Multiplies TTS/STT complexity, translation accuracy issues | English-only v1, add languages later |

## Feature Dependencies

```
[Push-to-talk]
    └──requires──> [Audio Capture (PyAudio)]
                       └──requires──> [STT (Faster Whisper)]
                                          └──feeds into──> [RAG Retrieval]
                                                               └──feeds into──> [LLM Generation]
                                                                                    └──feeds into──> [TTS (Piper)]
                                                                                    └──feeds into──> [Screen Display]

[Knowledge Base]
    └──feeds into──> [RAG Retrieval]
    └──feeds into──> [Screen Display] (images/diagrams)

[Project Recommendation] ──requires──> [Knowledge Base] + [LLM Generation]

[Follow-up Questions] ──requires──> [Conversation State] ──enhances──> [LLM Generation]

[Idle Screen] ──independent──> (no dependencies)
```

### Dependency Notes

- **STT requires Audio Capture:** Mic input must work before STT can process
- **RAG requires Knowledge Base:** Knowledge base must be populated before retrieval works
- **TTS is independent of display:** Can develop audio output and visual output in parallel
- **Project recommendation requires rich KB:** Needs project-to-tool mappings, not just tool docs

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Push-to-talk voice input — press button, speak question
- [ ] Speech-to-text transcription — accurate in lab environment
- [ ] Knowledge base with tool/equipment info — at least core tools covered
- [ ] RAG retrieval — find relevant knowledge for the question
- [ ] LLM answer generation — coherent, accurate spoken answer
- [ ] Text-to-speech output — natural-sounding response
- [ ] On-screen transcript — show question and answer text
- [ ] Graceful "I don't know" — don't hallucinate, admit gaps

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Step-by-step guidance with images — show equipment photos alongside voice guidance
- [ ] Safety warnings — proactive safety info for dangerous equipment
- [ ] Project recommendation — "I want to build X" → tool suggestions
- [ ] Idle/attract screen — show lab info when not in use
- [ ] Follow-up questions — multi-turn conversation within a session

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Multilingual support — add after English v1 is solid
- [ ] Usage analytics — track what students ask about most
- [ ] Admin dashboard — web interface for knowledge base management
- [ ] Equipment status integration — IoT or manual status updates

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Voice input (STT) | HIGH | HIGH | P1 |
| Spoken response (TTS) | HIGH | MEDIUM | P1 |
| Tool Q&A via RAG | HIGH | MEDIUM | P1 |
| On-screen transcript | MEDIUM | LOW | P1 |
| Push-to-talk | HIGH | LOW | P1 |
| Graceful "I don't know" | HIGH | LOW | P1 |
| Safety warnings | HIGH | LOW | P1 |
| Step-by-step with images | MEDIUM | MEDIUM | P2 |
| Project recommendation | MEDIUM | MEDIUM | P2 |
| Follow-up questions | MEDIUM | MEDIUM | P2 |
| Idle/attract screen | LOW | LOW | P2 |
| Multilingual | LOW | HIGH | P3 |
| Usage analytics | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Amazon Alexa | Google Assistant | Custom Makerspace Kiosks | Our Approach |
|---------|--------------|------------------|--------------------------|--------------|
| Voice interaction | Full NLU pipeline | Full NLU pipeline | Often text-only or simple menu | Local STT + LLM — flexible natural language |
| Domain knowledge | Skills/apps ecosystem | Google Knowledge Graph | Static FAQ or curated content | RAG over custom knowledge base |
| Always listening | Yes (wake word) | Yes (wake word) | Usually not | Push-to-talk (intentional) |
| Visual display | Echo Show has screen | Nest Hub has screen | Touchscreen kiosks common | Screen with transcript + visuals |
| Offline capability | No | No | Sometimes | Fully offline — key differentiator |
| Privacy | Cloud-processed | Cloud-processed | Varies | Fully local — no data leaves the lab |

## Sources

- Analysis of makerspace information systems and kiosk deployments
- Voice assistant UX research and design patterns
- Local LLM deployment guides and community benchmarks
- University makerspace operational patterns

---
*Feature research for: Local AI Voice Assistant for Makerspace*
*Researched: 2026-01-30*
