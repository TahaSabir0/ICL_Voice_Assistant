"""
Tests for the error handling and stability module.
"""

import pytest
from unittest.mock import MagicMock, patch
import time
import threading


class TestErrorCategorization:
    """Tests for error categorization."""
    
    def test_transient_error_connection(self):
        """Connection errors are categorized as transient."""
        from src.ui.error_handling import categorize_error, ErrorCategory
        
        error = ConnectionError("Connection refused")
        assert categorize_error(error) == ErrorCategory.TRANSIENT
    
    def test_transient_error_timeout(self):
        """Timeout errors are categorized as transient."""
        from src.ui.error_handling import categorize_error, ErrorCategory
        
        error = TimeoutError("Request timeout")
        assert categorize_error(error) == ErrorCategory.TRANSIENT
    
    def test_hardware_error_audio(self):
        """Audio device errors are categorized as hardware."""
        from src.ui.error_handling import categorize_error, ErrorCategory
        
        error = Exception("Audio device not found")
        assert categorize_error(error) == ErrorCategory.HARDWARE
    
    def test_fatal_error_memory(self):
        """Memory errors are categorized as fatal."""
        from src.ui.error_handling import categorize_error, ErrorCategory
        
        error = MemoryError("Out of memory")
        assert categorize_error(error) == ErrorCategory.FATAL
    
    def test_default_pipeline_error(self):
        """Unknown errors default to pipeline category."""
        from src.ui.error_handling import categorize_error, ErrorCategory
        
        error = ValueError("Some processing error")
        assert categorize_error(error) == ErrorCategory.PIPELINE


class TestRecoveryActions:
    """Tests for recovery action determination."""
    
    def test_fatal_error_shutdown(self):
        """Fatal errors should trigger shutdown."""
        from src.ui.error_handling import get_recovery_action, RecoveryAction
        
        error = MemoryError("Out of memory")
        action = get_recovery_action(error)
        assert action == RecoveryAction.SHUTDOWN
    
    def test_transient_error_retry(self):
        """Transient errors should retry on first attempt."""
        from src.ui.error_handling import get_recovery_action, RecoveryAction
        
        error = ConnectionError("Connection refused")
        action = get_recovery_action(error, retry_count=0)
        assert action == RecoveryAction.RETRY
    
    def test_transient_error_reset_after_retries(self):
        """Transient errors should reset after max retries."""
        from src.ui.error_handling import get_recovery_action, RecoveryAction
        
        error = ConnectionError("Connection refused")
        action = get_recovery_action(error, retry_count=5)
        assert action == RecoveryAction.RESET_STATE
    
    def test_hardware_error_restart(self):
        """Hardware errors should restart pipeline."""
        from src.ui.error_handling import get_recovery_action, RecoveryAction
        
        error = Exception("audio device error")
        action = get_recovery_action(error)
        assert action == RecoveryAction.RESTART_PIPELINE


class TestHealthMonitor:
    """Tests for HealthMonitor."""
    
    def test_initial_state(self):
        """Monitor starts in healthy state."""
        from src.ui.error_handling import HealthMonitor
        
        monitor = HealthMonitor(unhealthy_threshold=60.0)
        assert monitor.is_healthy
    
    def test_record_activity(self):
        """Recording activity updates timestamp and increments operations."""
        from src.ui.error_handling import HealthMonitor
        
        monitor = HealthMonitor()
        
        # Check initial state
        initial_ops = monitor._total_operations
        
        # Record activity
        monitor.record_activity()
        
        # Should increment operations
        assert monitor._total_operations == initial_ops + 1
    
    def test_record_error(self):
        """Errors are tracked."""
        from src.ui.error_handling import HealthMonitor
        
        monitor = HealthMonitor()
        monitor.record_error()
        monitor.record_error()
        
        assert monitor._error_count == 2
    
    def test_error_rate(self):
        """Error rate is calculated correctly."""
        from src.ui.error_handling import HealthMonitor
        
        monitor = HealthMonitor()
        monitor.record_activity()  # 1 operation
        monitor.record_activity()  # 2 operations
        monitor.record_error()     # 1 error
        
        assert monitor.error_rate == 50.0  # 1 error / 2 operations
    
    def test_reset_errors(self):
        """Error count can be reset."""
        from src.ui.error_handling import HealthMonitor
        
        monitor = HealthMonitor()
        monitor.record_error()
        monitor.record_error()
        monitor.reset_errors()
        
        assert monitor._error_count == 0
    
    def test_get_status(self):
        """Status includes all metrics."""
        from src.ui.error_handling import HealthMonitor
        
        monitor = HealthMonitor()
        monitor.record_activity()
        monitor.record_error()
        
        status = monitor.get_status()
        
        assert "healthy" in status
        assert "seconds_since_activity" in status
        assert "error_count" in status
        assert "total_operations" in status
        assert "error_rate" in status


class TestWatchdog:
    """Tests for Watchdog timer."""
    
    def test_watchdog_creation(self):
        """Watchdog can be created."""
        from src.ui.error_handling import Watchdog
        
        watchdog = Watchdog(timeout=10.0)
        assert watchdog is not None
        assert watchdog.timeout == 10.0
    
    def test_watchdog_ping(self):
        """Ping resets the watchdog timer."""
        from src.ui.error_handling import Watchdog
        
        watchdog = Watchdog(timeout=10.0)
        watchdog.start()
        
        time.sleep(0.1)
        initial_elapsed = time.time() - watchdog._last_ping
        
        watchdog.ping()
        new_elapsed = time.time() - watchdog._last_ping
        
        assert new_elapsed < initial_elapsed
        watchdog.stop()
    
    def test_watchdog_callback_on_timeout(self):
        """Watchdog calls timeout callback."""
        from src.ui.error_handling import Watchdog
        
        callback = MagicMock()
        watchdog = Watchdog(timeout=0.5, on_timeout=callback)
        watchdog.start()
        
        # Don't ping, let it timeout (wait longer than timeout + some buffer)
        time.sleep(1.5)
        
        callback.assert_called()
        watchdog.stop()


class TestMemoryMonitor:
    """Tests for MemoryMonitor."""
    
    def test_memory_monitor_creation(self):
        """Memory monitor can be created."""
        from src.ui.error_handling import MemoryMonitor
        
        monitor = MemoryMonitor(warning_threshold_mb=1000.0)
        assert monitor is not None
    
    def test_set_baseline(self):
        """Baseline can be set."""
        from src.ui.error_handling import MemoryMonitor
        
        monitor = MemoryMonitor()
        monitor.set_baseline()
        
        # Baseline should be set (may be 0 if psutil not available)
        assert monitor._baseline is not None
    
    def test_check_memory(self):
        """Memory check returns status dict."""
        from src.ui.error_handling import MemoryMonitor
        
        monitor = MemoryMonitor()
        status = monitor.check_memory()
        
        assert "current_mb" in status
        assert "warning" in status
