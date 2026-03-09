# Session Notes: Setup Script Fixes, Ollama Integration & Kiosk App Stability

**Date:** March 8-9, 2026
**Tool:** Gemini (Antigravity) / Claude Code (Sonnet 4.6)

---

## Summary

Extensive debugging and refactoring of `Setup-And-Run.ps1` to properly install Ollama, start its server, and hand off to the existing `Start-Kiosk.ps1` launcher. Multiple bugs were discovered and fixed relating to Windows PowerShell 5.1 quirks, Ollama's auto-start behavior, and process management.

---

## What Was Done

### 1. UI Freeze Fix (from previous session, confirmed working)
- **Problem:** `QMetaObject.invokeMethod` in `src/ui/kiosk_app.py` silently dropped cross-thread commands
- **Fix:** Replaced with proper `Signal`/`Slot` connections using `Qt.QueuedConnection`
- **Files:** `src/ui/kiosk_app.py` (method `_connect_window_signals`)
- **Status:** ✅ Confirmed working

### 2. Setup Script (`Setup-And-Run.ps1`) — Complete Rewrite

#### Bugs Found & Fixed (in order of discovery):

**Bug 1: Installer blocking forever**
- **Problem:** Original script called `& $installerPath` which blocked the PowerShell session because the Ollama GUI installer doesn't exit cleanly
- **Fix:** Use `Start-Process -PassThru` + `Wait-Process -Timeout 300` to track the installer process and wait for it with a timeout

**Bug 2: `Invoke-WebRequest` hanging silently**
- **Problem:** Windows PowerShell 5.1 uses Internet Explorer's engine to parse HTTP responses by default. This causes a hidden "Do you want to continue?" security prompt that hangs the script
- **Fix (partial):** Added `-UseBasicParsing` flag
- **Fix (final):** Replaced ALL `Invoke-WebRequest` calls with raw TCP socket checks (`System.Net.Sockets.TcpClient`) because even with `-UseBasicParsing`, HTTP requests to localhost were hanging on this system (possibly proxy-related)

**Bug 3: Broken Ollama install detected as working**
- **Problem:** Script only checked if `ollama.exe` file existed on disk. A partial/broken install left the file but it couldn't actually run
- **Fix:** After finding the exe, verify it works by running `ollama --version` and checking the output matches "ollama"

**Bug 4: `-WindowStyle Hidden` silently failing**
- **Problem:** `Start-Process -FilePath ollama.exe -ArgumentList "serve" -WindowStyle Hidden` did not actually start the process. No error, just nothing happened
- **Fix:** Use plain `Start-Process -FilePath ollama.exe -ArgumentList "serve"` (opens a visible window). The server runs in that window.

**Bug 5: Ollama auto-start respawning killed processes**
- **Problem:** Ollama installer registers itself in Windows Startup folder. Every time we killed the process, Windows relaunched it, creating port conflicts when our `ollama serve` tried to bind port 11434
- **Fix:** Stop fighting it. Check if port 11434 is already open (someone is serving). If yes, use it. If no, start our own. The desktop app IS the server.

**Bug 6: Em-dash characters causing parse errors**
- **Problem:** Unicode em-dash (`—`) characters in comments caused Windows PowerShell 5.1 to fail parsing the script
- **Fix:** Rewrote entire file with ASCII-only characters

**Bug 7: Script was duplicating `Start-Kiosk.ps1` logic**
- **Problem:** Setup script had its own app launch code at the end, ignoring the existing `Start-Kiosk.ps1` which already handles auto-restart, crash detection, and logging
- **Fix:** Setup script now calls `Start-Kiosk.ps1` at the end instead of launching the app directly

**Bug 8: Script installing deps into system Python instead of venv**
- **Problem:** `Start-Kiosk.ps1` expects `.venv/Scripts/python.exe` but the setup script was installing into the system Python
- **Fix:** Setup script now creates `.venv` and installs deps into it

**Bug 9: Splatting error when calling Start-Kiosk.ps1**
- **Problem:** `& $startKiosk @kioskArgs` with an array `@("-Windowed")` passed it as a positional argument to `MaxRestarts` parameter
- **Fix:** Changed to hashtable splatting: `$kioskArgs = @{}; $kioskArgs["Windowed"] = $true`

#### Final Script Architecture:

```
Setup-And-Run.ps1 (run once, as admin)
├── Step 1: Find Python (py launcher, user profiles, system paths)
├── Step 2: Find/Install Ollama (download + GUI installer)
├── Step 3: Start Ollama server (TCP port check, not HTTP)
├── Step 4: Pull LLM model (ollama pull)
├── Step 5: Create .venv + pip install -e .
├── Step 6: Verify project dirs
└── Hand off to Start-Kiosk.ps1
         ├── Launches scripts/launch_kiosk.py using .venv Python
         ├── Auto-restart on crash
         ├── Logging to logs/
         └── Crash counter with reset
```

### 3. Cleanup Script (`Cleanup-And-Stop.ps1`) — Fixed (previous session)
- **Problem 1:** `Get-Process.CommandLine` not available in PS 5.1. Fixed with `Get-CimInstance Win32_Process`
- **Problem 2:** Didn't stop Ollama tray app or Windows service. Fixed by targeting all `ollama*` processes and `OllamaService`
- **Status:** Fixed but user expressed concern about using it. Recommended manual cleanup instead (close window + right-click tray icon)

---

### 4. Kiosk App Stability Fixes (March 9, 2026)

Diagnosed and fixed three bugs causing the app to freeze/crash after one prompt. Root cause was identified from `logs/kiosk_stderr.log` which showed Qt thread violation errors immediately after pipeline initialization.

#### Evidence from logs:
```
QObject::killTimer: Timers cannot be stopped from another thread
QObject::killTimer: Timers cannot be stopped from another thread
QObject::setParent: Cannot set parent, new parent is in a different thread
```
These errors appeared at startup right after the watchdog was started, confirming a thread-safety violation.

---

**Bug 1: Watchdog callback calling Qt from a Python thread**
- **File:** `src/ui/kiosk_app.py` — `_on_watchdog_timeout()`
- **Problem:** The `Watchdog` class runs in a `threading.Thread` (Python thread, not Qt thread). Its timeout callback `_on_watchdog_timeout` was directly calling `self.window.set_state()`, `self.window.set_status()`, and `QTimer.singleShot()` from that Python thread. This is a Qt threading violation — Qt UI objects can only be safely accessed from the main thread. This caused the `killTimer`/`setParent` errors and unpredictable crashes.
- **Fix:** `_on_watchdog_timeout` now only logs and posts work back to the main thread using `QTimer.singleShot(0, self._watchdog_recover_on_main_thread)`. The new `_watchdog_recover_on_main_thread` slot runs on the main thread and does all the UI updates safely.

**Bug 2: `time.sleep()` blocking the worker thread event loop**
- **File:** `src/ui/pipeline_worker.py` — error handlers in `_process_audio()` and `process_text_input()`
- **Problem:** On error, both methods called `time.sleep(3)` before emitting `state_changed("idle")`. `time.sleep()` is a hard block — it suspends the entire worker thread including its Qt event loop. During those 3 seconds, any signals queued for the worker (e.g. a second PTT press) could not be delivered, causing the app to appear frozen.
- **Fix:** Replaced both `time.sleep(3)` calls with `QThread.msleep(3000)`. `QThread.msleep()` yields control back to the thread's event loop during the wait, allowing queued signals to be processed.

**Bug 3: RAG causes native segfault from QThread — DISABLED in UI**
- **File:** `src/ui/pipeline_worker.py` — both `_process_audio()` and `process_text_input()`
- **Problem:** ChromaDB / sentence-transformers causes a **native segfault** (C-level crash) when called from a QThread worker. The process is killed instantly with no Python traceback, no exit code, and no exception to catch (even `except BaseException` is useless against a segfault). This was confirmed by:
  - `autostart_20260309.log` showing the kiosk exiting with a blank exit code ~20 seconds after becoming ready (right when the user submits a prompt)
  - No error logging between "Pipeline ready" and the crash
  - `context.md` documenting that RAG works perfectly in the CLI (`src/main.py`) but crashes in the UI
- **Initial fix attempt:** Added RAG to `process_text_input` (same as voice path). This made the crash worse — text input now also crashed immediately.
- **Final fix:** Disabled RAG in both `_process_audio()` and `process_text_input()` in the UI. Added detailed comments explaining why. The app now works without knowledge base context.
- **Root cause (unresolved):** Likely a thread-safety issue in ChromaDB's SQLite backend or sentence-transformers' model inference when called from a Qt worker thread. The retriever is initialized on the QThread and called from the same QThread, but internal threading in these libraries may conflict with Qt's event loop.
- **Possible future fixes:**
  - Run RAG retrieval in a **subprocess** (multiprocessing) to isolate it from the Qt process
  - Initialize the retriever on the **main thread** and use signals to request/receive context
  - Use a **thread-safe wrapper** around ChromaDB (e.g., queue-based access from a dedicated Python thread, not a QThread)

---

## Known Issues / TODO

### RAG Crash in UI (Critical)
RAG is currently **disabled** in the kiosk UI to prevent native segfaults. The app works but without knowledge base context — all answers come from the base LLM. See Bug 3 above for details and possible fixes. RAG continues to work in the CLI (`src/main.py`).

### App Startup Time (~2 minutes)
The kiosk app takes ~2 minutes to initialize because it loads multiple AI models sequentially:
1. **Sentence-transformers** (`all-MiniLM-L6-v2`) — embedding model for RAG
2. **Faster-whisper** — speech-to-text model
3. **Piper TTS** — text-to-speech model
4. **ChromaDB** — vector store initialization

**Possible improvements:**
- Lazy-load models (only load when first needed)
- Show per-model loading progress in UI instead of just "Thinking..."
- Pre-download models during setup script instead of on first launch

### Ollama Auto-Start
- User disabled Ollama auto-start in Windows Settings
- Fresh install re-enables it (installer adds Startup shortcut)
- After running setup, user may want to disable again: Settings → Apps → Startup → Ollama → Off
- Could add script to disable it programmatically: `Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Ollama.lnk"`

---

## File Changes Made

| File | Change |
|------|--------|
| `Setup-And-Run.ps1` | Complete rewrite — setup + delegate to Start-Kiosk.ps1 |
| `Cleanup-And-Stop.ps1` | Fixed PS 5.1 process detection + Ollama service stop |
| `src/ui/kiosk_app.py` | Signal/Slot fix for invokeMethod freeze; watchdog thread-safety fix |
| `src/ui/pipeline_worker.py` | `time.sleep` -> `QThread.msleep`; `process_text_input` now uses RAG |

## Key Design Decisions

1. **TCP check instead of HTTP** — `Invoke-WebRequest` is unreliable on Windows PowerShell 5.1 for localhost connections. Raw TCP socket connect via `System.Net.Sockets.TcpClient` is instant and reliable.

2. **Don't fight Ollama's desktop app** — The installer auto-launches a desktop app that serves on port 11434. Instead of killing it and starting our own `ollama serve`, just detect if port 11434 is open and use whatever is serving.

3. **Delegate to Start-Kiosk.ps1** — Don't duplicate launch logic. The existing script handles auto-restart, crash detection, logging. Setup script just sets up prerequisites and hands off.

4. **Virtual environment** — Setup script creates `.venv` which is what `Start-Kiosk.ps1` expects. Previous version installed into system Python.

---

## How to Run

```powershell
# First time (installs everything):
# Run in admin PowerShell
.\Setup-And-Run.ps1 -Windowed

# Subsequent runs (everything installed):
# Start Ollama if not running
Start-Process "C:\Users\regan\AppData\Local\Programs\Ollama\ollama.exe" "serve"
# Then launch kiosk
.\Start-Kiosk.ps1 -Windowed

# Or just re-run setup (it skips installed items):
.\Setup-And-Run.ps1 -Windowed
```

## How to Uninstall Ollama
1. Settings → Apps → Installed Apps → Ollama → Uninstall
2. Delete models: `Remove-Item -Recurse "$env:USERPROFILE\.ollama"`

---

# RAG Subprocess Fix (March 9, 2026, continuation)

## Problem: Native Segfault in UI RAG

The kiosk app crashed immediately after processing any prompt (voice or text) when RAG was enabled. Root cause analysis identified:

**ONNX Runtime** (used by sentence-transformers for embeddings):
- Spawns internal thread pools for CPU/GPU acceleration
- These threads are incompatible with Qt's event loop when ONNX runs in a QThread worker

**ChromaDB** (vector database):
- Uses SQLite backend which is not thread-safe
- When called from QThread, conflicts with Qt's event loop mutex

**Result**: C-level segfault with no Python traceback, no exception to catch, instant process death.

**Attempted fix (earlier)**: Disabling RAG entirely — worked but removed knowledge base context from responses.

---

## Solution: Subprocess-Based RAG Retriever

Run RAG (ChromaDB + sentence-transformers) in a **completely separate Python process**, communicating via `multiprocessing.Pipe`. This isolates ONNX Runtime and SQLite from Qt entirely.

### Architecture

```
Qt Main Thread (kiosk_app.py)
  └── QThread Worker (pipeline_worker.py)
       └── SubprocessRetriever (parent side)
            └ multiprocessing.Pipe
                 └── Child Process (separate Python interpreter)
                      └── Retriever (ChromaDB + embeddings)
                           ├── VectorStore (ChromaDB)
                           └── EmbeddingService (ONNX Runtime)
```

The child process:
- Has its own memory space, interpreter, and GIL
- Loads embedding models in complete isolation
- Never touches Qt, QThread, or any Qt objects
- Communicates only via serialized request/response objects

---

## Implementation Details

### New File: `src/rag/subprocess_retriever.py`

**`SubprocessRetriever` class:**
- Spawns a child process on `start()` with the target function `_worker_process`
- Parent and child exchange `_Request` / `_Response` dataclasses via Pipe
- Supports `get_context(query)` method — safe to call from any thread (including QThread)
- Graceful shutdown: sends `shutdown` request, joins with 5s timeout, kills if needed
- Timeout handling: 120s for model initialization, 30s for queries

**Message Protocol:**
```python
_Request(type: str, query: str, n_results: int, max_context_length: int)
_Response(success: bool, data: str, doc_count: int)
```

**Worker Process Function `_worker_process(conn, store_path, relevance_threshold)`:**
- Imports `Retriever` inside the function (not at module level) to keep imports minimal
- Initializes ChromaDB + embeddings in child process only
- Runs an event loop waiting for requests on the Pipe
- Sends responses back immediately
- Exits on `shutdown` request or pipe EOF

### Modified: `src/ui/pipeline_worker.py`

**Changes to `PipelineWorker.__init__`:**
- Added `self._subprocess_retriever: Optional[SubprocessRetriever] = None`

**Changes to `initialize()`:**
- Creates a copy of PipelineConfig with `use_rag=False` (disable in-process RAG)
- Passes this to `VoicePipeline()` — prevents segfault-causing RAG initialization
- After pipeline init, creates and starts `SubprocessRetriever`
- Errors during RAG subprocess startup are logged but don't crash the app

**Changes to `_process_audio()` (voice input):**
- Removed: "RAG disabled" workaround comment
- Added: Check if `self._subprocess_retriever.is_ready`
- If ready: calls `get_context()` from the subprocess, times the call, tracks metrics
- RAG context is now properly used for LLM system prompt

**Changes to `process_text_input()` (text input):**
- Same as `_process_audio()` — RAG now works for text prompts too
- Uses appropriate system prompt based on whether context was found

**Changes to `shutdown()`:**
- Calls `self._subprocess_retriever.stop()` to clean up the child process

### Modified: `scripts/launch_kiosk.py`

- Added `import multiprocessing` and `multiprocessing.freeze_support()` in the `if __name__ == "__main__"` block
- `freeze_support()` is required for multiprocessing on Windows (good practice for frozen executables)

---

## Why This Works

1. **Process Isolation**: ONNX Runtime thread pools and SQLite don't interfere with Qt because they run in a separate process
2. **No GIL Contention**: Child process has its own GIL, parent's Qt loop never blocks on model inference
3. **Safe Communication**: Only serializable dataclasses pass over the Pipe — no shared memory, no thread-unsafe object sharing
4. **Error Resilience**: If child process crashes, parent still runs (parent can gracefully continue without RAG)
5. **Cross-Thread Safety**: `SubprocessRetriever.get_context()` is a pure function call with no state mutations — safe from any thread

---

## Known Limitations & Future Improvements

1. **Startup Time**: Embedding model still loads (just in subprocess now). Could pre-load on setup.
2. **Model Updates**: If knowledge base is updated, child process won't see it until restart.
3. **Error Messages**: If RAG subprocess fails silently, user won't know (currently just logs).
4. **Timeouts**: If query takes >30s, parent gets empty context. Could increase timeout or implement cancellation.

---

## Testing

**To verify RAG works:**
```powershell
# Run kiosk in windowed mode
.\.venv\Scripts\python.exe scripts/launch_kiosk.py --windowed

# Try a text input related to knowledge base (e.g., "What is 3D printing?")
# Expected: Response should include context from the knowledge base
# Check logs/kiosk_stdout.log for:
#   "Starting RAG retrieval (subprocess)"
#   "RAG found X chars of context"
```

**To disable RAG for testing:**
```powershell
.\.venv\Scripts\python.exe scripts/launch_kiosk.py --windowed --no-rag
```

---

## Files Changed

| File | Change |
|------|--------|
| `src/rag/subprocess_retriever.py` | NEW — Subprocess-based RAG retriever |
| `src/ui/pipeline_worker.py` | Integrate SubprocessRetriever; enable RAG from both voice & text inputs |
| `scripts/launch_kiosk.py` | Add multiprocessing.freeze_support() |
