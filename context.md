# ICL Voice Assistant - Implementation Guide

**For: AI Coding Agents**
**Project:** Local voice assistant for the Innovation & Creativity Lab (ICL) at Gettysburg College
**Approach:** Step-by-step implementation with user verification at each checkpoint

---

## Project Overview

This project builds a fully local voice assistant kiosk for the Innovation & Creativity Lab at Gettysburg College. Students will be able to ask questions about lab equipment (3D printers, laser cutters, CNC machines, sewing/embroidery, VR systems, etc.) and get spoken answers with usage guidance and safety information.

**Core Requirements:**
- Everything runs locally (no cloud APIs)
- Hardware: Single server acts as both backend and kiosk display
- Interaction: Push-to-talk button → speak question → hear answer
- Knowledge: RAG-based system with markdown knowledge base

---

## Planning Documents Reference

All planning documents are in the `.planning/` folder. These documents contain the decisions, research, and roadmap that guide implementation.

### Core Planning Files

#### 1. **PROJECT.md** - Project Definition
**Purpose:** The single source of truth for what this project is and why it exists.

**Contains:**
- Project vision and goals
- Target users (ICL students and staff)
- Success criteria
- Key constraints (fully local, specific hardware, no cloud)
- Key decisions made during planning

**How to use it:**
- Read this FIRST to understand the big picture
- Reference when making architectural decisions
- Check constraints before choosing libraries or approaches

---

#### 2. **REQUIREMENTS.md** - Detailed Requirements
**Purpose:** Specific, testable requirements organized by category.

**Contains:**
- VOICE-XX: Voice pipeline requirements (STT, LLM, TTS)
- KB-XX: Knowledge base requirements (content, RAG, retrieval)
- UI-XX: User interface requirements (kiosk, push-to-talk, display)
- KBM-XX: Knowledge base management requirements

**How to use it:**
- Check requirements before implementing each feature
- Use requirement IDs when writing commit messages
- Verify implementation satisfies each requirement

**Example:**
```
VOICE-01: System must transcribe speech using Faster Whisper (local)
→ When implementing STT, use Faster Whisper, not cloud APIs
```

---

#### 3. **ROADMAP.md** - Implementation Roadmap
**Purpose:** The execution plan broken into 3 phases, each with detailed plans.

**Contains:**
- Phase 1: Voice Pipeline (STT → LLM → TTS working end-to-end)
- Phase 2: Knowledge Base & RAG (ICL tool documentation + retrieval)
- Phase 3: Kiosk UI & Integration (Full-screen UI + deployment)
- Success criteria for each phase
- Detailed sub-plans for each phase (01-01, 01-02, 01-03, etc.)

**How to use it:**
- **CRITICAL:** Implement phases IN ORDER (1 → 2 → 3)
- Each phase has 3 sub-plans that should be done sequentially
- Success criteria define when a phase is complete
- Don't move to next phase until current phase passes all success criteria

**Example Phase 1 Structure:**
```
Phase 1: Voice Pipeline
├── Plan 01-01: Set up project, install dependencies, configure Ollama
├── Plan 01-02: Implement audio capture + STT + TTS
└── Plan 01-03: Wire full pipeline + benchmark performance

Success Criteria:
✓ User can record audio and get transcription
✓ System generates spoken answer using local LLM/TTS
✓ End-to-end latency < 8 seconds
✓ All models run on local GPU/CPU without errors
```

---

#### 4. **STATE.md** - Project Progress Tracking
**Purpose:** Current status and progress metrics.

**Contains:**
- Current phase and plan
- Progress percentage
- Recent activity
- Pending todos
- Known blockers

**How to use it:**
- Check at start of each session to see where you left off
- Update after completing each plan
- Log blockers or concerns as they arise

---

#### 5. **config.json** - Build Configuration
**Purpose:** Project configuration and settings.

**Contains:**
- Whether to commit planning docs to git
- Project metadata

**How to use it:**
- Reference for project settings
- Generally don't need to modify

---

### Research Documents (`.planning/research/`)

These documents contain research findings from the planning phase. They inform implementation decisions but are READ-ONLY references.

#### **STACK.md** - Technology Stack Analysis
- Recommended libraries and tools
- Why each technology was chosen
- Version compatibility considerations

**Key findings:**
- Python 3.11+ for better async support
- Faster Whisper for STT (fastest local option)
- Ollama for LLM hosting (Llama 3.1 8B fits in VRAM budget)
- Piper TTS for speech synthesis
- ChromaDB for vector storage
- PySide6 for kiosk UI

---

#### **ARCHITECTURE.md** - System Architecture
- Component breakdown (STT, LLM, TTS, RAG, UI)
- Data flow diagrams
- Module organization
- VRAM budget analysis

**Key insights:**
- Pipeline: Audio → Faster Whisper → Ollama → Piper → Speakers
- Threaded architecture (UI thread separate from processing)
- RAG flow: Query → Embed → ChromaDB → Retrieve → Augment prompt → LLM

---

#### **FEATURES.md** - Feature Analysis
- Core features breakdown
- Feature dependencies
- Implementation priorities

---

#### **PITFALLS.md** - Common Issues & Solutions
- Known challenges in local voice assistants
- VRAM management strategies
- Latency optimization tips
- Error handling patterns
- Security considerations

**Critical warnings:**
- Don't load all models simultaneously without VRAM checks
- Handle microphone permissions gracefully
- Implement proper model unloading to prevent memory leaks
- Never expose raw LLM without safety guardrails

---

#### **SUMMARY.md** - Research Summary
- High-level synthesis of all research
- Key decisions and rationale
- Trade-offs analysis

---

## Implementation Workflow

### Step-by-Step Approach

**YOU MUST FOLLOW THIS WORKFLOW:**

1. **Start with Phase 1**
   - Read ROADMAP.md Phase 1 section completely
   - Understand the 3 sub-plans (01-01, 01-02, 01-03)

2. **For each sub-plan, break it into small steps**
   - Example for Plan 01-01:
     - Step 1: Create Python virtual environment
     - Step 2: Install core dependencies (faster-whisper, ollama-python)
     - Step 3: Pull Llama 3.1 model via Ollama
     - Step 4: Verify installation with simple test

3. **Implement ONE step at a time**
   - Write the code for that step only
   - Keep changes focused and minimal

4. **After each step: STOP and verify with user**
   - Show what you implemented
   - Explain what it does
   - Run a test if applicable
   - **WAIT FOR USER CONFIRMATION before continuing**

5. **User confirms → Move to next step**
   - If approved: Continue to next step
   - If issues: Fix them before proceeding
   - If blocked: Document in STATE.md and discuss with user

6. **After completing a sub-plan: Full verification**
   - Run all tests for that sub-plan
   - Verify against success criteria
   - Commit with clear message
   - Get user sign-off before next sub-plan

7. **After completing a phase: Comprehensive verification**
   - Test ALL success criteria from ROADMAP.md
   - Document results
   - Get user approval before moving to next phase

### Commit Message Format

Use clear, descriptive commit messages:

```
feat(voice): implement audio capture with sounddevice

- Added AudioCapture class with start/stop methods
- Configured 16kHz sampling rate for Whisper compatibility
- Implements VOICE-01 requirement
```

### Progress Tracking

After completing each sub-plan, update STATE.md:
- Increment progress
- Note what was completed
- Log any deviations or issues
- Update current position

---

## Phase Breakdown

### Phase 1: Voice Pipeline

**Goal:** Get audio in → transcription → LLM response → audio out working

**Plans:**

**01-01: Environment Setup**
- Create project structure
- Install dependencies (faster-whisper, ollama, piper-tts)
- Configure Ollama with Llama 3.1
- Verify each component loads successfully

**01-02: Component Implementation**
- Build audio capture module (record from mic)
- Build STT module (Faster Whisper wrapper)
- Build TTS module (Piper wrapper)
- Test each component individually

**01-03: Pipeline Integration**
- Wire components together
- Implement full conversation flow
- Add latency measurements
- Benchmark and optimize
- Verify < 8 second response time

**Success Criteria (all must pass):**
1. ✓ User can record audio via microphone by pressing a key → transcription appears
2. ✓ System generates spoken answer using local LLM and TTS
3. ✓ End-to-end latency < 8 seconds
4. ✓ All models run on local GPU/CPU without errors

---

### Phase 2: Knowledge Base & RAG

**Goal:** Build ICL tool knowledge base and add RAG retrieval

**Plans:**

**02-01: Knowledge Base Creation**
- Create markdown structure for ICL tools
- Write documentation for major tools (3D printers, laser cutters, CNC, etc.)
- Include safety information for each tool
- Organize by category

**02-02: Document Ingestion Pipeline**
- Build markdown parser
- Implement chunking strategy
- Set up ChromaDB
- Create embeddings and ingest documents
- Verify retrieval works

**02-03: RAG Integration**
- Integrate retrieval into LLM pipeline
- Engineer system prompt for RAG
- Handle "I don't know" cases
- Test accuracy with sample questions

**Success Criteria (all must pass):**
1. ✓ Knowledge base contains all major ICL tools
2. ✓ System retrieves relevant content when asked about specific tools
3. ✓ Responses include safety information when applicable
4. ✓ System admits "I don't know" for out-of-scope questions
5. ✓ Can update knowledge by editing markdown and re-ingesting

---

### Phase 3: Kiosk UI & Integration

**Goal:** Build full-screen kiosk interface and deploy

**Plans:**

**03-01: Kiosk UI Development**
- Build PySide6 full-screen window
- Create push-to-talk button
- Add state indicators (idle/listening/thinking)
- Display conversation transcript

**03-02: Pipeline Integration**
- Connect voice pipeline to UI
- Implement threaded processing
- Add error handling and recovery
- Show processing states in real-time

**03-03: Stability & Deployment**
- Test 24-hour continuous operation
- Fix memory leaks
- Add auto-restart on crash
- Configure kiosk mode startup
- Document deployment process

**Success Criteria (all must pass):**
1. ✓ Application launches in full-screen kiosk mode
2. ✓ Push-to-talk button works → shows "listening" state
3. ✓ After speaking → shows "thinking" → displays Q&A
4. ✓ Answer is spoken and displayed simultaneously
5. ✓ Runs stably for 24 hours without crashes

---

## Key Principles

### 1. **Incremental Development**
- Small steps, frequent verification
- Don't try to implement entire phase at once
- Each step should take 5-15 minutes of work

### 2. **User as QA Gate**
- User must approve each step before continuing
- If something doesn't work, fix it immediately
- Don't accumulate technical debt

### 3. **Test Early, Test Often**
- After each step, run a quick test
- After each sub-plan, run comprehensive tests
- After each phase, run full integration tests

### 4. **Follow the Roadmap**
- Phases MUST be done in order (dependencies exist)
- Don't skip steps or combine sub-plans
- Success criteria are not optional

### 5. **Reference the Research**
- When stuck, check PITFALLS.md for known issues
- Use ARCHITECTURE.md for design decisions
- Follow STACK.md for technology choices

### 6. **Document as You Go**
- Update STATE.md after each sub-plan
- Commit with clear messages
- Note any deviations or decisions made

---

## Quick Start Checklist

Before starting implementation:

- [ ] Read PROJECT.md (understand the vision)
- [ ] Read REQUIREMENTS.md (know what to build)
- [ ] Read ROADMAP.md Phase 1 (understand first phase)
- [ ] Read ARCHITECTURE.md (understand system design)
- [ ] Read STACK.md (know which libraries to use)
- [ ] Read PITFALLS.md (avoid common mistakes)

Starting Phase 1, Plan 01-01:

- [ ] Propose step-by-step breakdown to user
- [ ] Get user approval on steps
- [ ] Implement Step 1
- [ ] Verify with user → proceed
- [ ] Repeat until sub-plan complete
- [ ] Full verification → commit → move to 01-02

---

## Example: Starting Phase 1, Plan 01-01

**Agent says to user:**

> "I'm ready to start Phase 1, Plan 01-01: Environment Setup. Here's my proposed breakdown:
>
> **Step 1:** Create project structure (`src/`, `tests/`, `requirements.txt`)
> **Step 2:** Set up Python virtual environment
> **Step 3:** Install core dependencies (faster-whisper, ollama-python, sounddevice, piper-tts)
> **Step 4:** Install and configure Ollama
> **Step 5:** Pull Llama 3.1 8B model
> **Step 6:** Write simple test script to verify each component loads
>
> Does this breakdown look good? Should I proceed with Step 1?"

**User confirms → Agent implements Step 1 → Shows result → Waits for approval → Continues**

---

## Important Files Locations

```
ICL_Voice_Assistant/
├── .planning/
│   ├── PROJECT.md              ← Read first: Project definition
│   ├── REQUIREMENTS.md         ← Requirements checklist
│   ├── ROADMAP.md              ← Implementation phases (FOLLOW THIS)
│   ├── STATE.md                ← Current progress (UPDATE THIS)
│   ├── config.json             ← Build settings
│   └── research/
│       ├── SUMMARY.md          ← Research overview
│       ├── STACK.md            ← Technology choices
│       ├── ARCHITECTURE.md     ← System design
│       ├── FEATURES.md         ← Feature breakdown
│       └── PITFALLS.md         ← Common issues & solutions
└── context.md                  ← This file (your guide)
```

---

## Success Metrics

**Phase 1 Complete When:**
- Voice pipeline works end-to-end
- Latency < 8 seconds
- All models run locally without errors
- User can have a basic conversation

**Phase 2 Complete When:**
- Knowledge base contains all ICL tools
- RAG retrieval returns accurate information
- Safety information included in responses
- "I don't know" handling works

**Phase 3 Complete When:**
- Kiosk UI fully functional
- 24-hour stability test passes
- Deployed and ready for student use

---

## Getting Help

If you encounter issues:

1. **Check PITFALLS.md** - Solution might be documented
2. **Check ARCHITECTURE.md** - Verify design approach is correct
3. **Ask the user** - Explain the blocker and get guidance
4. **Log in STATE.md** - Document the issue for future reference

---

**Remember:** The user is your QA gate. After every step, pause and verify. This ensures nothing breaks and progress is steady.

Good luck! 🚀
