"""
Quick test to verify UI doesn't freeze after first request.

This test runs the kiosk app and simulates text input to ensure
the threading fix works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.ui.kiosk_app import KioskApplication


def test_sequential_requests():
    """Test that we can make multiple requests without freezing."""
    
    app = KioskApplication(
        fullscreen=False,
        use_rag=False,  # RAG disabled as requested
        enable_watchdog=False  # Don't need watchdog for this test
    )
    
    def send_test_messages():
        """Send a few test messages to verify no freeze."""
        if not app.window:
            print("Window not ready yet, retrying...")
            QTimer.singleShot(500, send_test_messages)
            return
        
        print("\n=== Sending first test message ===")
        app.window.text_submitted.emit("What is 2 plus 2?")
        
        # Send second message after 8 seconds (enough time for first to complete)
        QTimer.singleShot(8000, lambda: send_second_message())
    
    def send_second_message():
        """Send second message to test if UI recovered."""
        print("\n=== Sending second test message ===")
        app.window.text_submitted.emit("Tell me a short joke.")
        
        # Send third message after another 8 seconds
        QTimer.singleShot(8000, lambda: send_third_message())
    
    def send_third_message():
        """Send third message to confirm fix works consistently."""
        print("\n=== Sending third test message ===")
        app.window.text_submitted.emit("What is the capital of France?")
        
        # Exit after this completes
        QTimer.singleShot(8000, lambda: exit_test())
    
    def exit_test():
        """Exit the test."""
        print("\n=== Test complete! If you got here, the fix worked! ===")
        app.shutdown()
        QApplication.instance().quit()
    
    # Wait for pipeline to initialize before sending messages
    QTimer.singleShot(3000, send_test_messages)
    
    return app.run()


if __name__ == "__main__":
    print("Starting UI freeze test...")
    print("This will send 3 sequential text messages to verify the fix.")
    print("Watch for 'Turn complete' messages between each request.\n")
    
    sys.exit(test_sequential_requests())
