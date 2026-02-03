# UI Freeze Bug - Analysis and Fix

## Problem Summary

The kiosk UI was freezing after the first text input request. The system would process the first request successfully, but subsequent requests would not be processed, leaving the UI stuck in the "thinking" state indefinitely.

## Root Cause

The issue was in `src/ui/kiosk_app.py` in the `_on_text_submitted` method (lines 388-403). The code was using `QMetaObject.invokeMethod()` to call `process_text_input` on the worker thread:

```python
QMetaObject.invokeMethod(
    self.pipeline_thread.worker,
    "process_text_input",
    Qt.ConnectionType.QueuedConnection,
    Q_ARG(str, text)
)
```

### Why This Failed

`QMetaObject.invokeMethod()` with `QueuedConnection` and arguments (`Q_ARG`) is **unreliable** for cross-thread method invocations in PySide6, especially after the first call. This is a known limitation of the Qt meta-object system when used with Python.

The symptoms:
1. First request works fine (method gets invoked successfully)
2. Subsequent requests fail silently (method never gets called)
3. UI remains in "thinking" state forever (no completion signal)
4. No errors or exceptions are thrown (silent failure)

This is the **exact same bug** that occurred at the end of Phase 2, which was fixed by switching to signal-based connections.

## The Fix

Replaced the `QMetaObject.invokeMethod()` approach with a **direct signal-to-slot connection**:

### Changes Made:

1. **Modified `_connect_window_signals()` in `kiosk_app.py`:**
   ```python
   def _connect_window_signals(self):
       """Connect window signals to pipeline."""
       self.window.ptt_pressed.connect(self._on_ptt_pressed)
       self.window.ptt_released.connect(self._on_ptt_released)
       # Connect text submission directly to worker (thread-safe signal)
       self.window.text_submitted.connect(
           self.pipeline_thread.worker.process_text_input,
           Qt.ConnectionType.QueuedConnection
       )
   ```

2. **Removed the broken `_on_text_submitted()` method** - No longer needed since we connect the signal directly

3. **Updated `pipeline_worker.py`** to emit `transcription_ready` signal for text input so the user message appears in the UI

## Why This Works

Signal-to-slot connections in Qt are the **recommended and reliable** way to communicate across threads. When you connect a signal to a slot with `QueuedConnection`:

- Qt handles all the thread-safety automatically
- Events are properly queued in the target thread's event loop
- The mechanism is robust and tested (unlike `invokeMethod` with Python)
- Works consistently for all invocations, not just the first

## Testing

Created `tests/test_ui_freeze_fix.py` which:
- Sends 3 sequential text messages
- Waits for each to complete before sending the next
- Verifies the UI remains responsive throughout
- Exits successfully if all messages are processed

To run the test:
```bash
python tests/test_ui_freeze_fix.py
```

Watch for "Turn complete" messages between each request - if you see all three, the fix is working!

## Similar Issues to Watch For

This same pattern could cause problems elsewhere. **Never** use `QMetaObject.invokeMethod()` with arguments for cross-thread calls. Always use signals and slots:

### ❌ Wrong (Don't do this):
```python
QMetaObject.invokeMethod(
    worker, "some_method",
    Qt.QueuedConnection,
    Q_ARG(str, arg)
)
```

### ✅ Correct (Do this instead):
```python
# Define signal in window/sender
some_signal = Signal(str)

# Connect to worker slot
some_signal.connect(worker.some_method, Qt.QueuedConnection)

# Emit when needed
some_signal.emit(arg)
```

## Related Issues

- This is the same bug pattern that was fixed in Phase 2
- Push-to-talk (PTT) button already uses this pattern correctly
- All pipeline state signals already use direct connections
- This was the only remaining case of the broken pattern

## Status

**FIXED** ✅

The UI should now handle multiple sequential requests without freezing.
