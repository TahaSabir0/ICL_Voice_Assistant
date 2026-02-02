"""
Unit tests for the Kiosk UI components.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Ensure QApplication exists for testing
@pytest.fixture(scope="session")
def app():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestPushToTalkButton:
    """Tests for PushToTalkButton widget."""
    
    def test_initial_state_is_idle(self, app):
        """Button starts in idle state."""
        from src.ui.widgets import PushToTalkButton
        
        button = PushToTalkButton()
        assert button.state == "idle"
        assert button.isEnabled()
    
    def test_set_state_listening(self, app):
        """Button can be set to listening state."""
        from src.ui.widgets import PushToTalkButton
        
        button = PushToTalkButton()
        button.set_state("listening")
        
        assert button.state == "listening"
    
    def test_set_state_thinking_disables_button(self, app):
        """Thinking state disables the button."""
        from src.ui.widgets import PushToTalkButton
        
        button = PushToTalkButton()
        button.set_state("thinking")
        
        assert button.state == "thinking"
        assert not button.isEnabled()
    
    def test_set_state_speaking_disables_button(self, app):
        """Speaking state disables the button."""
        from src.ui.widgets import PushToTalkButton
        
        button = PushToTalkButton()
        button.set_state("speaking")
        
        assert button.state == "speaking"
        assert not button.isEnabled()
    
    def test_return_to_idle_enables_button(self, app):
        """Returning to idle re-enables the button."""
        from src.ui.widgets import PushToTalkButton
        
        button = PushToTalkButton()
        button.set_state("thinking")
        button.set_state("idle")
        
        assert button.state == "idle"
        assert button.isEnabled()
    
    def test_recording_started_signal(self, app):
        """Signal emitted when entering listening state."""
        from src.ui.widgets import PushToTalkButton
        
        button = PushToTalkButton()
        callback = MagicMock()
        button.recording_started.connect(callback)
        
        button.set_state("listening")
        
        callback.assert_called_once()
    
    def test_recording_stopped_signal(self, app):
        """Signal emitted when leaving listening state."""
        from src.ui.widgets import PushToTalkButton
        
        button = PushToTalkButton()
        callback = MagicMock()
        button.recording_stopped.connect(callback)
        
        button.set_state("listening")
        button.set_state("thinking")
        
        callback.assert_called_once()


class TestStateIndicator:
    """Tests for StateIndicator widget."""
    
    def test_initial_state(self, app):
        """Indicator starts in idle state."""
        from src.ui.widgets import StateIndicator
        
        indicator = StateIndicator()
        assert indicator.state == "idle"
    
    def test_set_all_states(self, app):
        """Can set to all valid states."""
        from src.ui.widgets import StateIndicator
        
        indicator = StateIndicator()
        
        states = ["idle", "listening", "transcribing", "retrieving", 
                  "thinking", "speaking", "error"]
        
        for state in states:
            indicator.set_state(state)
            assert indicator.state == state


class TestConversationView:
    """Tests for ConversationView widget."""
    
    def test_add_user_message(self, app):
        """Can add user messages."""
        from src.ui.widgets import ConversationView
        
        view = ConversationView()
        view.add_message("user", "Hello!")
        
        assert len(view._messages) == 1
        assert view._messages[0].role == "user"
        assert view._messages[0].text == "Hello!"
    
    def test_add_assistant_message(self, app):
        """Can add assistant messages."""
        from src.ui.widgets import ConversationView
        
        view = ConversationView()
        view.add_message("assistant", "Hi there!")
        
        assert len(view._messages) == 1
        assert view._messages[0].role == "assistant"
    
    def test_multiple_messages(self, app):
        """Can add multiple messages."""
        from src.ui.widgets import ConversationView
        
        view = ConversationView()
        view.add_message("user", "Question 1")
        view.add_message("assistant", "Answer 1")
        view.add_message("user", "Question 2")
        view.add_message("assistant", "Answer 2")
        
        assert len(view._messages) == 4
    
    def test_clear_messages(self, app):
        """Can clear all messages."""
        from src.ui.widgets import ConversationView
        
        view = ConversationView()
        view.add_message("user", "Hello")
        view.add_message("assistant", "Hi")
        view.clear()
        
        assert len(view._messages) == 0
    
    def test_thinking_indicator(self, app):
        """Thinking indicator can be shown/hidden."""
        from src.ui.widgets import ConversationView
        
        view = ConversationView()
        view.show()  # Need to show parent widget for child visibility to work
        
        view.show_thinking()
        # After showing, the widget should be added and started
        assert view._thinking.parent() is not None  # Added to layout
        
        view.hide_thinking()
        # After hiding, the timer should be stopped
        assert not view._thinking._timer.isActive()


class TestKioskWindow:
    """Tests for the main KioskWindow."""
    
    def test_window_creation(self, app):
        """Window can be created in windowed mode."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        assert window is not None
        window.close()
    
    def test_set_state(self, app):
        """Window state can be updated."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        window.set_state("listening")
        
        assert window.state_indicator.state == "listening"
        assert window.ptt_button.state == "listening"
        window.close()
    
    def test_add_messages(self, app):
        """Messages can be added to conversation."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        window.add_user_message("Hello")
        window.add_assistant_message("Hi there!")
        
        assert len(window.conversation_view._messages) == 2
        window.close()
    
    def test_set_status(self, app):
        """Status bar text can be updated."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        window.set_status("Processing request...")
        
        assert window._status_label.text() == "Processing request..."
        window.close()
    
    def test_clear_conversation(self, app):
        """Conversation can be cleared."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        window.add_user_message("Test")
        window.add_assistant_message("Response")
        window.clear_conversation()
        
        assert len(window.conversation_view._messages) == 0
        window.close()
    
    def test_ptt_signals(self, app):
        """PTT signals are emitted."""
        from src.ui import KioskWindow
        
        window = KioskWindow(fullscreen=False)
        
        pressed_callback = MagicMock()
        released_callback = MagicMock()
        
        window.ptt_pressed.connect(pressed_callback)
        window.ptt_released.connect(released_callback)
        
        # Simulate button press/release
        window.ptt_button.pressed.emit()
        window.ptt_button.released.emit()
        
        pressed_callback.assert_called()
        released_callback.assert_called()
        window.close()
