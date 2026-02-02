"""
Test script for the Kiosk UI.

Run this to preview the kiosk interface in windowed mode.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.ui import KioskWindow


def demo_states(window: KioskWindow):
    """Demonstrate the different states."""
    states = [
        ("idle", 2000),
        ("listening", 3000),
        ("transcribing", 1500),
        ("retrieving", 1500),
        ("thinking", 2000),
        ("speaking", 3000),
        ("idle", 0),
    ]
    
    delay = 0
    for state, duration in states:
        QTimer.singleShot(delay, lambda s=state: window.set_state(s))
        delay += duration
    
    # Demo messages
    QTimer.singleShot(3000, lambda: window.add_user_message(
        "How do I use the 3D printer?"
    ))
    QTimer.singleShot(8500, lambda: window.add_assistant_message(
        "To use the Prusa MK4 3D printer, you'll first want to make sure "
        "you've completed the required safety training. Then you can export "
        "your model as an STL file and slice it using PrusaSlicer. The printer "
        "is located in the fabrication area of the ICL."
    ))


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create window in windowed mode for testing
    window = KioskWindow(fullscreen=False)
    window.show()
    
    # Run demo after a short delay
    QTimer.singleShot(1000, lambda: demo_states(window))
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
