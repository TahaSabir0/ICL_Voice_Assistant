# Technical Insights & Architectural Review (March 2026)

This document captures the critical findings from the codebase review and the strategy for reaching a fully stable, production-ready state for the ICL Voice Assistant.

## 1. The "UI Freeze" Root Cause
The primary instability in the current prototype is a communication failure between the **UI Thread** (Main) and the **Worker Thread** (Background).

### The Problem: `QMetaObject.invokeMethod`
The application currently uses `QMetaObject.invokeMethod()` as a shortcut to send commands (like "Start Recording" or "Process Text") from the UI to the background worker.
*   **The Bug:** In the PySide6 (Python) implementation of Qt, this method frequently fails to correctly serialize arguments across thread boundaries. 
*   **The Result:** The command is "dropped" silently. The UI enters a waiting state (e.g., "Thinking..."), but the Worker Thread never receives the instruction to begin. This creates a permanent hang that requires a manual restart.

### The Solution: Standard Signal/Slot Connections
All cross-thread communication must be refactored to use formal `Signal` and `Slot` definitions.
*   **Mechanism:** Define signals in the UI classes (e.g., `start_recording_signal = Signal()`) and connect them to worker slots using `Qt.QueuedConnection`.
*   **Benefit:** This is the native, thread-safe, and guaranteed delivery mechanism in Qt. It eliminates the "silent drop" issue entirely.

---

## 2. Deployment & Setup Bottlenecks
The project is "code-complete" but not "one-click functional." It currently lacks an automated bootstrap process.

### Current Manual Requirements:
1.  **Ollama Installation:** Must be manually downloaded and installed on the host OS.
2.  **Model Pulling:** The specific model (`llama3.1:8b-instruct-q4_K_M`) must be manually pulled via terminal.
3.  **Environment Sync:** Dependencies must be manually managed.

### Proposed Solution: "Bootstrap" Script
A master PowerShell script (`Setup-And-Run.ps1`) should be implemented to:
*   Check for Ollama and trigger an install if missing.
*   Automatically run `ollama pull` for the required model.
*   Verify the local ChromaDB vector store in `data/vector_store/`.
*   Launch the application only after these pre-requisites are met.

---

## 3. UI/UX Enhancements
Based on lab environment research, two key UX improvements were identified:

### Simultaneous Text & Audio with Mute Toggle
In a noisy makerspace, audio is not always reliable. 
*   **Behavior:** The UI should display the text response bubble **immediately** upon LLM completion, while simultaneously triggering the TTS audio.
*   **Mute Feature:** A software-level "Mute" toggle should be added to the header. 
*   **Implementation:** The `PipelineWorker` should check a `is_muted` flag in `PipelineConfig` before calling the audio playback component, allowing the user to read in silence if preferred.

### Loading & "Heavy Lifting" Feedback
Loading 5GB+ of AI models into VRAM causes a temporary "Not Responding" state in Windows.
*   **Solution:** Improve the Splash Screen or add a dedicated "Loading Models" overlay to keep the UI process "alive" and inform the user that a large one-time load is occurring.

---

## 4. Pipeline Threading Logic
The current design uses a **single Worker Thread** for the entire AI pipeline (STT -> RAG -> LLM -> TTS).

*   **Why Sequential?** The components are chained (Step B needs the output of Step A).
*   **Hardware Constraint:** Keeping the heavy components (Whisper and Llama) in a single sequential thread prevents GPU VRAM collisions and "Out of Memory" errors.
*   **Future Optimization:** If lower latency is required, the LLM and TTS could be split into two threads to allow for **sentence-by-sentence streaming**, where the assistant begins speaking the first sentence while the second is still being generated.

---

## 5. Summary of Needed "Surgery"
To move from **Prototype** to **Production**:
1.  **Refactor:** Replace all `invokeMethod` calls with `Signals`.
2.  **Automate:** Create the Ollama/Model bootstrap script.
3.  **Enhance:** Add the Mute Toggle and improved loading feedback.
