"""
Tests for the pipeline integration with the UI.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer


# Ensure QApplication exists for testing
@pytest.fixture(scope="session")
def app():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestPipelineWorker:
    """Tests for PipelineWorker."""
    
    def test_worker_creation(self, app):
        """Worker can be created."""
        from src.ui.pipeline_worker import PipelineWorker
        from src.pipeline import PipelineConfig
        
        config = PipelineConfig(use_rag=False)
        worker = PipelineWorker(config)
        
        assert worker is not None
        assert worker.config.use_rag == False
    
    def test_worker_signals_exist(self, app):
        """Worker has all required signals."""
        from src.ui.pipeline_worker import PipelineWorker
        
        worker = PipelineWorker()
        
        # Check all signals exist
        assert hasattr(worker, 'state_changed')
        assert hasattr(worker, 'transcription_ready')
        assert hasattr(worker, 'response_ready')
        assert hasattr(worker, 'error_occurred')
        assert hasattr(worker, 'initialized')
        assert hasattr(worker, 'metrics_available')
        assert hasattr(worker, 'turn_complete')
    
    def test_signal_connections(self, app):
        """Signals can be connected to slots."""
        from src.ui.pipeline_worker import PipelineWorker
        
        worker = PipelineWorker()
        
        callback = MagicMock()
        worker.state_changed.connect(callback)
        
        # Emit a signal manually
        worker.state_changed.emit("listening")
        
        callback.assert_called_once_with("listening")


class TestPipelineThread:
    """Tests for PipelineThread."""
    
    def test_thread_creation(self, app):
        """Thread can be created."""
        from src.ui.pipeline_worker import PipelineThread
        from src.pipeline import PipelineConfig
        
        config = PipelineConfig(use_rag=False)
        thread = PipelineThread(config)
        
        assert thread is not None
        assert thread.worker is not None
    
    def test_thread_has_worker(self, app):
        """Thread contains a worker."""
        from src.ui.pipeline_worker import PipelineThread
        
        thread = PipelineThread()
        
        assert hasattr(thread, 'worker')
        assert thread.worker is not None


class TestKioskApplication:
    """Tests for KioskApplication."""
    
    def test_app_creation(self, app):
        """Application can be created."""
        from src.ui.kiosk_app import KioskApplication
        
        kiosk = KioskApplication(fullscreen=False, use_rag=False)
        
        assert kiosk is not None
        assert kiosk.fullscreen == False
        assert kiosk.use_rag == False
    
    def test_app_defaults(self, app):
        """Application has sensible defaults."""
        from src.ui.kiosk_app import KioskApplication
        
        kiosk = KioskApplication()
        
        assert kiosk.fullscreen == True  # Default is fullscreen
        assert kiosk.use_rag == True     # Default is RAG enabled
    
    def test_app_model_config(self, app):
        """Application accepts model configuration."""
        from src.ui.kiosk_app import KioskApplication
        
        kiosk = KioskApplication(llm_model="llama3.2:1b")
        
        assert kiosk.llm_model == "llama3.2:1b"


class TestIntegration:
    """Integration tests for UI/Pipeline connection."""
    
    def test_window_state_updates(self, app):
        """Window state can be updated from signal."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        
        # Simulate state change from pipeline
        states = ["listening", "transcribing", "retrieving", "thinking", "speaking", "idle"]
        
        for state in states:
            window.set_state(state)
            assert window.state_indicator.state == state
        
        window.close()
    
    def test_message_flow(self, app):
        """Messages flow correctly through the window."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        
        # Simulate message flow
        window.add_user_message("How do I use the laser cutter?")
        window.add_assistant_message(
            "To use the laser cutter, first complete the safety training..."
        )
        
        assert len(window.conversation_view._messages) == 2
        assert window.conversation_view._messages[0].role == "user"
        assert window.conversation_view._messages[1].role == "assistant"
        
        window.close()
    
    def test_error_handling_display(self, app):
        """Errors are displayed in status bar."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        
        # Simulate error
        window.set_status("Error: Connection failed")
        window.set_state("error")
        
        assert window.state_indicator.state == "error"
        assert "Error" in window._status_label.text()
        
        window.close()
