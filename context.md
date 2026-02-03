# ICL Voice Assistant - Context & Status

**Current Source of Truth** - *Last Updated: Feb 2, 2026*

This document supersedes all content in the `.planning/` directory. Refer to this file for the actual state of the project, known issues, and how to run the code.

---

## 1. Project Overview

**Goal:** A fully local voice assistant kiosk for the Innovation & Creativity Lab (ICL) at Gettysburg College.  
**Function:** Students ask questions about lab equipment (3D printers, laser cutters, etc.) and receive spoken answers via a full-screen interface.  
**Constraint:** Runs entirely on local hardware (no cloud APIs).

### Tech Stack
*   **Language:** Python 3.11+
*   **Dependency Manager:** `uv`
*   **UI:** PySide6 (Qt)
*   **STT:** Faster Whisper (Local)
*   **LLM:** Ollama (Llama 3.1 8B)
*   **TTS:** Piper (Local)
*   **RAG:** ChromaDB (Vector Store)

---

## 2. Current Project Status

| Phase | Component | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Voice Pipeline | ✅ Working | STT -> LLM -> TTS pipeline functions correctly. |
| **Phase 2** | CLI & RAG | ✅ Working | `src/main.py` works perfectly with RAG retrieval. |
| **Phase 3** | Kiosk UI | ❌ Broken | Graphic Interface Integration is unstable. |

### 🚨 Critical Issues (Phase 3)

The project is currently stuck at Phase 3 (UI Integration).

1.  **UI Freezes after First Request:**
    *   When RAG is disabled, the UI successfully handles the first voice/text prompt and speaks the response.
    *   **Immediately after the response, the app becomes unresponsive.**
    *   *Suspected Cause:* Threading/Event loop issue in `kiosk_app.py` or `window` signal handling. (Note: A fix involving direct signal connections was attempted in `kiosk_app.py`, but behavior needs verification).

2.  **RAG Crash in UI:**
    *   Enabling RAG in the UI causes the application to **shut down immediately** after transcribing the first prompt.
    *   *Contrast:* RAG works perfectly in the CLI (`src/main.py`), suggesting the issue is specific to how the UI thread interacts with the Retriever/ChromaDB.

---

## 3. How to Run & Test

### Prerequisites
*   Ollama running (`ollama serve`) with `llama3.1:8b-instruct-q4_K_M` pulled.
*   Python 3.11+ and `uv` installed.

### 🟢 Running the Working Version (Phase 2)
To verify the core logic and RAG system are working:
```powershell
uv run python src/main.py
```
*Expected Behavior:* Console-based interaction. You speak/type, it retrieves context, and responds via audio.

### 🔴 Running the Broken Version (Phase 3 UI)
To reproduce the UI freeze/crash:
```powershell
# Run with RAG (Crashes)
uv run python src/ui/kiosk_app.py

# Run WITHOUT RAG (Freezes after 1 turn)
uv run python src/ui/kiosk_app.py --no-rag
```

### Running Tests
```powershell
# Run complete test suite
uv run pytest

# Run specific UI freeze test (verifies the attempted fix)
uv run python tests/test_ui_freeze_fix.py
```

---

## 4. Key Directory Structure

*   **`src/`** - Application Source
    *   **`main.py`**: Entry point for CLI (Phase 2) - **Reference this for working logic.**
    *   **`pipeline/`**: Core logic (STT, LLM, TTS, RAG). Shared by implementation.
    *   **`ui/`**: Kiosk implementation.
        *   `kiosk_app.py`: Main Qt Application entry point.
        *   `kiosk_window.py`: UI Layout and Widget definitions.
        *   `pipeline_worker.py`: QThread worker for handling voice processing off the main thread.
*   **`knowledge_base/`**: Markdown files containing lab equipment documentation.
*   **`data/`**: ChromaDB persistence directory and temp audio files.
*   **`.planning/`**: ⚠️ **DEPRECATED**. Do not use. Information here is outdated.

---

## 5. Development Notes & Pitfalls

*   **Threading is Fragile:** The interaction between PySide6 `QThread` and the heavy ML models (Whisper/Ollama) is the primary source of instability.
*   **Signal Slots:** Do NOT use `QMetaObject.invokeMethod` for cross-thread calls with arguments; it fails silently. Use direct Signal-Slot connections.
*   **Environment:** The app relies on specific audio devices. If `sounddevice` fails, check default system mic/speakers.
*   **Ollama:** Must be running in the background. If the app hangs on "Thinking" indefinitely without CPU usage, check if Ollama is responsive.
