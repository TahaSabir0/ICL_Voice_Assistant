# Pitfalls Research

**Domain:** Local AI Voice Assistant with RAG
**Researched:** 2026-01-30
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: VRAM Exhaustion / OOM Crashes

**What goes wrong:**
Application crashes with CUDA out-of-memory errors when STT, LLM, and embeddings all compete for GPU memory. Especially common during the transition between STT and LLM inference.

**Why it happens:**
Developers load all models simultaneously without accounting for peak VRAM usage. VRAM fragmentation after repeated model loading/unloading makes the problem worse over time.

**How to avoid:**
- Budget VRAM carefully: Faster Whisper medium (~2GB) + Ollama Llama 8B Q4 (~5GB) + embeddings (~0.1GB) = ~7GB total, well within 24GB
- Use Ollama for LLM — it manages VRAM automatically
- Keep models loaded persistently rather than loading/unloading per request
- Monitor with nvidia-smi during development

**Warning signs:**
- Sporadic crashes under load
- Increasing response times over hours of operation
- CUDA error messages in logs

**Phase to address:** Phase 1 (foundation) — validate VRAM budget before building anything else

---

### Pitfall 2: Unacceptable Pipeline Latency

**What goes wrong:**
Total time from "student finishes speaking" to "assistant starts responding" exceeds 8-10 seconds. Students walk away or assume it's broken.

**Why it happens:**
Each pipeline stage (STT + retrieval + LLM generation + TTS) adds latency. Without optimization, total can easily hit 15-20 seconds. Developers test with short phrases and don't notice until real usage.

**How to avoid:**
- Target <5 seconds end-to-end for typical questions
- Use faster-whisper (not openai-whisper) — 4x faster
- Use quantized LLM (Q4_K_M) — faster inference
- Stream LLM response to TTS (start speaking before full answer generated)
- Use Piper TTS (CPU-based, fast) rather than GPU-based TTS
- Benchmark each stage independently to find bottlenecks

**Warning signs:**
- Individual stage taking >2 seconds
- Students asking "is it working?" or pressing button again
- Long silences between question and answer

**Phase to address:** Phase 1 (foundation) — measure latency from the start, not as an afterthought

---

### Pitfall 3: Poor RAG Retrieval Quality

**What goes wrong:**
Assistant retrieves wrong or irrelevant knowledge base chunks, leading to incorrect answers. Student asks about the laser cutter and gets information about the 3D printer.

**Why it happens:**
- Chunks are too large (entire documents) or too small (fragments without context)
- No metadata filtering (all documents treated equally)
- Embedding model not suited for the query style
- Knowledge base documents are poorly structured

**How to avoid:**
- Chunk size 200-500 tokens with 50-token overlap
- Add metadata to chunks: tool_name, category, document_type
- Use metadata filtering in retrieval (narrow search by category when possible)
- Test retrieval with real student questions before connecting LLM
- Structure knowledge base docs consistently (one tool per file, standard sections)

**Warning signs:**
- Assistant gives correct-sounding but wrong answers
- Retrieved chunks are from unrelated tools
- LLM frequently says "based on the available information" (hedging because context is poor)

**Phase to address:** Phase 2 (knowledge base + RAG) — test retrieval quality in isolation before LLM

---

### Pitfall 4: Hallucinated Safety Information

**What goes wrong:**
LLM generates plausible but incorrect safety instructions for equipment like CNC machines or laser cutters. Student follows bad advice and risks injury.

**Why it happens:**
LLM has general training knowledge about these tools that may be wrong for the specific equipment in the lab. If RAG retrieval fails to find relevant safety docs, LLM falls back to training data.

**How to avoid:**
- System prompt explicitly instructs: "Only provide safety information from the knowledge base. If safety information is not in your context, direct students to lab staff."
- Include safety information prominently in knowledge base documents
- Test with safety-related queries specifically
- Consider a safety disclaimer in UI for all tool-related answers

**Warning signs:**
- Assistant gives safety advice not found in knowledge base
- Safety answers lack specific details about the lab's equipment models
- No "consult staff" fallback when safety info is missing

**Phase to address:** Phase 2 (knowledge base) — safety content must be in KB, and Phase 3 (LLM prompting) — system prompt must handle missing safety info

---

### Pitfall 5: Microphone Issues in Noisy Environment

**What goes wrong:**
STT accuracy drops significantly because the makerspace is noisy — 3D printers humming, CNC running, people talking. Whisper transcribes background noise as speech or misinterprets words.

**Why it happens:**
Developers test in quiet environments. Consumer microphones pick up everything. No noise suppression applied to audio before STT.

**How to avoid:**
- Use a directional microphone or headset-style mic close to the speaker
- Apply noise gate / voice activity detection before sending to STT
- Test with actual lab ambient noise during development
- Consider recording a sample of lab noise and testing STT against it
- Faster Whisper's VAD (voice activity detection) filter helps

**Warning signs:**
- STT accuracy drops when lab equipment is running
- Transcription includes phantom words or fragments
- Students need to repeat themselves frequently

**Phase to address:** Phase 1 (audio capture) — validate mic quality and noise handling early

---

### Pitfall 6: Knowledge Base Becomes Stale

**What goes wrong:**
Information about tools, procedures, or availability becomes outdated. New equipment added without updating KB. Students get incorrect guidance.

**Why it happens:**
No easy workflow for updating the knowledge base. Developer has to remember to update, re-chunk, and re-embed documents. No reminder system.

**How to avoid:**
- Make knowledge base files simple markdown — easy to edit
- Create a simple ingestion script: edit markdown → run script → KB updated
- Document the update process clearly
- Keep knowledge base in git for change tracking

**Warning signs:**
- Students report outdated information
- New equipment not mentioned by assistant
- Procedures described don't match current practice

**Phase to address:** Phase 2 (knowledge base) — build simple update workflow from the start

---

### Pitfall 7: Application Crashes After Hours of Running

**What goes wrong:**
Kiosk application becomes unresponsive or crashes after running for hours/days. Memory leaks, GPU memory fragmentation, or thread deadlocks accumulate.

**Why it happens:**
ML models and audio processing can leak memory. PyAudio streams not properly closed. Qt event loop blocked. No watchdog or auto-restart mechanism.

**How to avoid:**
- Implement proper resource cleanup after each interaction
- Add a watchdog/health check that restarts the application if unresponsive
- Set up systemd/service auto-restart on crash
- Monitor memory usage over time during testing
- Close and reopen audio streams per interaction rather than keeping them open

**Warning signs:**
- Gradual memory increase over time (check with monitoring)
- Application freezing after being idle for hours
- Audio device errors after many interactions

**Phase to address:** Phase 4 (kiosk deployment) — stability and auto-restart

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoded model paths | Quick setup | Breaks on different machines | MVP only — parameterize for v1.x |
| No error handling in pipeline | Faster development | Crashes on edge cases | Never — basic error handling from day 1 |
| Single-thread pipeline | Simpler code | UI freezes during processing | Never — use threading from the start |
| No logging | Less code | Can't debug issues in production | Never — add structured logging early |
| Embedded config values | No config files | Hard to tune without code changes | MVP only — extract to config file |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading models per request | 10-30s delay per question | Load at startup, keep resident | Immediately — every interaction |
| Large chunk sizes in RAG | Poor retrieval, irrelevant answers | 200-500 token chunks with overlap | When KB has >5 documents |
| Unquantized LLM | Slow inference, high VRAM | Use Q4_K_M quantization | Immediately with 8B+ models |
| No streaming TTS | Long pause before speaking | Stream first sentence while generating rest | Noticeable with answers >2 sentences |
| Synchronous Ollama calls | Blocks entire pipeline | Use async HTTP calls | Immediately |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| LLM prompt injection via voice | Student tricks assistant into ignoring system prompt | Robust system prompt, input sanitization, test adversarial inputs |
| Knowledge base contains sensitive info | Assistant reveals staff-only information | Review KB content, separate public/private knowledge |
| No input length limits | Extremely long audio recordings consume resources | Cap recording duration (e.g., 30 seconds max) |
| Ollama API exposed on network | Anyone on network can query the LLM | Bind Ollama to localhost only |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No visual feedback during processing | Students think it's frozen, press button again | Show processing animation, state indicators |
| Long uninterrupted TTS output | Students zone out during long spoken answers | Break into paragraphs, pause between sections |
| No indication of what to ask | Students don't know the assistant's capabilities | Show example questions on idle screen |
| Tiny text on transcript | Hard to read from standing distance | Large font, high contrast, readable at 3-4 feet |

## "Looks Done But Isn't" Checklist

- [ ] **STT:** Works in quiet room but not tested with lab ambient noise — test with real noise
- [ ] **RAG:** Returns results but quality not validated — test with 20+ real student questions
- [ ] **TTS:** Produces audio but volume not calibrated for lab environment — test at actual location
- [ ] **UI:** Looks good on development monitor but not tested at kiosk viewing distance
- [ ] **Pipeline:** Works for simple questions but not tested with long/complex/ambiguous queries
- [ ] **Stability:** Runs for 5 minutes in testing but not validated for 24-hour continuous operation
- [ ] **Knowledge Base:** Has content but not reviewed for accuracy by lab staff

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| VRAM exhaustion | LOW | Switch to smaller model, adjust quantization |
| Poor latency | MEDIUM | Profile each stage, swap models, add streaming |
| Bad RAG quality | MEDIUM | Re-chunk documents, tune retrieval parameters, add metadata |
| Hallucinated safety info | LOW | Update system prompt, add safety docs to KB |
| Mic noise issues | LOW | Swap microphone hardware, add VAD filtering |
| Stale knowledge base | LOW | Update docs, re-run ingestion |
| Application instability | MEDIUM | Add watchdog, fix memory leaks, add auto-restart |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| VRAM exhaustion | Phase 1 (foundation) | nvidia-smi shows stable VRAM under load |
| Pipeline latency | Phase 1 (foundation) | End-to-end <5 seconds measured |
| RAG quality | Phase 2 (knowledge base) | 80%+ retrieval accuracy on test queries |
| Safety hallucination | Phase 2 + 3 (KB + LLM) | Safety queries return KB content or "ask staff" |
| Mic noise | Phase 1 (audio) | STT accuracy >90% with lab background noise |
| Stale KB | Phase 2 (KB management) | Update workflow documented and tested |
| Long-running stability | Phase 4 (deployment) | 24-hour continuous operation test passes |

## Sources

- Local LLM deployment post-mortems and community discussions
- Voice assistant development guides
- RAG pipeline optimization literature
- GPU memory management for ML inference
- Makerspace safety and kiosk deployment patterns

---
*Pitfalls research for: Local AI Voice Assistant with RAG*
*Researched: 2026-01-30*
