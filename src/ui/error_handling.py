"""
Error Handling and Recovery Module.

Provides robust error handling, recovery mechanisms, and logging
for the kiosk application.
"""

import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from functools import wraps
import threading
import time


# Setup logging
def setup_logging(log_dir: Optional[Path] = None, level: int = logging.INFO):
    """
    Configure logging for the kiosk application.
    
    Args:
        log_dir: Directory for log files (default: ./logs)
        level: Logging level
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
    
    log_dir.mkdir(exist_ok=True)
    
    # Log file with date
    log_file = log_dir / f"kiosk_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    
    # Set specific levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    
    return log_file


# Get module logger
logger = logging.getLogger(__name__)


class RecoveryAction:
    """Defines a recovery action to take after an error."""
    
    CONTINUE = "continue"       # Log and continue
    RETRY = "retry"             # Retry the operation
    RESET_STATE = "reset"       # Reset to idle state
    RESTART_PIPELINE = "restart"  # Restart the pipeline
    SHUTDOWN = "shutdown"       # Graceful shutdown


class ErrorCategory:
    """Categories of errors for different handling strategies."""
    
    TRANSIENT = "transient"     # Temporary errors (network, timeout)
    PIPELINE = "pipeline"       # Pipeline processing errors
    HARDWARE = "hardware"       # Audio/hardware errors
    FATAL = "fatal"             # Unrecoverable errors


def categorize_error(error: Exception) -> str:
    """
    Categorize an error for appropriate handling.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Error category string
    """
    error_type = type(error).__name__
    error_msg = str(error).lower()
    
    # Network/connection errors are transient
    if any(x in error_type.lower() for x in ["connection", "timeout", "network"]):
        return ErrorCategory.TRANSIENT
    
    if any(x in error_msg for x in ["connection", "refused", "timeout"]):
        return ErrorCategory.TRANSIENT
    
    # Audio device errors
    if any(x in error_msg for x in ["audio", "device", "microphone", "speaker"]):
        return ErrorCategory.HARDWARE
    
    # Memory errors are fatal
    if "memory" in error_msg or isinstance(error, MemoryError):
        return ErrorCategory.FATAL
    
    # Default to pipeline error
    return ErrorCategory.PIPELINE


def get_recovery_action(error: Exception, retry_count: int = 0) -> str:
    """
    Determine the appropriate recovery action for an error.
    
    Args:
        error: The exception that occurred
        retry_count: Number of retries already attempted
        
    Returns:
        Recovery action to take
    """
    category = categorize_error(error)
    
    if category == ErrorCategory.FATAL:
        return RecoveryAction.SHUTDOWN
    
    if category == ErrorCategory.TRANSIENT and retry_count < 3:
        return RecoveryAction.RETRY
    
    if category == ErrorCategory.HARDWARE:
        return RecoveryAction.RESTART_PIPELINE
    
    if retry_count >= 3:
        return RecoveryAction.RESET_STATE
    
    return RecoveryAction.RESET_STATE


def with_error_handling(recovery_callback: Optional[Callable] = None):
    """
    Decorator for adding error handling to methods.
    
    Args:
        recovery_callback: Optional callback to handle recovery
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
                
                if recovery_callback:
                    action = get_recovery_action(e)
                    recovery_callback(e, action)
                
                raise
        return wrapper
    return decorator


class HealthMonitor:
    """
    Monitors the health of the kiosk application.
    
    Tracks:
    - Last successful operation timestamp
    - Error count
    - Memory usage
    - Response times
    """
    
    def __init__(self, unhealthy_threshold: float = 300.0):
        """
        Initialize the health monitor.
        
        Args:
            unhealthy_threshold: Seconds of inactivity before considered unhealthy
        """
        self.unhealthy_threshold = unhealthy_threshold
        self._last_activity = time.time()
        self._error_count = 0
        self._total_operations = 0
        self._lock = threading.Lock()
        
    def record_activity(self):
        """Record a successful activity."""
        with self._lock:
            self._last_activity = time.time()
            self._total_operations += 1
    
    def record_error(self):
        """Record an error occurrence."""
        with self._lock:
            self._error_count += 1
    
    def reset_errors(self):
        """Reset the error count."""
        with self._lock:
            self._error_count = 0
    
    @property
    def seconds_since_activity(self) -> float:
        """Get seconds since last activity."""
        return time.time() - self._last_activity
    
    @property
    def is_healthy(self) -> bool:
        """Check if the system is healthy."""
        return self.seconds_since_activity < self.unhealthy_threshold
    
    @property
    def error_rate(self) -> float:
        """Get error rate as percentage."""
        if self._total_operations == 0:
            return 0.0
        return (self._error_count / self._total_operations) * 100
    
    def get_status(self) -> dict:
        """Get current health status."""
        return {
            "healthy": self.is_healthy,
            "seconds_since_activity": self.seconds_since_activity,
            "error_count": self._error_count,
            "total_operations": self._total_operations,
            "error_rate": self.error_rate,
        }


class MemoryMonitor:
    """
    Monitors memory usage to prevent leaks.
    """
    
    def __init__(self, warning_threshold_mb: float = 2000.0):
        """
        Initialize memory monitor.
        
        Args:
            warning_threshold_mb: Memory usage threshold for warnings (MB)
        """
        self.warning_threshold = warning_threshold_mb * 1024 * 1024  # Convert to bytes
        self._baseline: Optional[int] = None
        
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            # psutil not available
            return 0
    
    def set_baseline(self):
        """Set the baseline memory usage."""
        self._baseline = self.get_memory_usage()
        logger.info(f"Memory baseline set: {self._baseline / 1024 / 1024:.1f} MB")
    
    def check_memory(self) -> dict:
        """
        Check current memory status.
        
        Returns:
            Dict with memory status
        """
        current = self.get_memory_usage()
        
        status = {
            "current_mb": current / 1024 / 1024,
            "warning": current > self.warning_threshold,
        }
        
        if self._baseline:
            growth = current - self._baseline
            status["growth_mb"] = growth / 1024 / 1024
            status["growth_percent"] = (growth / self._baseline) * 100
        
        if status.get("warning"):
            logger.warning(f"High memory usage: {status['current_mb']:.1f} MB")
        
        return status


class Watchdog:
    """
    Watchdog timer for detecting system hangs.
    
    Runs in a background thread and triggers a callback if the
    application doesn't check in within the timeout period.
    """
    
    def __init__(
        self, 
        timeout: float = 60.0,
        on_timeout: Optional[Callable] = None
    ):
        """
        Initialize the watchdog.
        
        Args:
            timeout: Seconds before triggering timeout
            on_timeout: Callback to invoke on timeout
        """
        self.timeout = timeout
        self.on_timeout = on_timeout
        self._last_ping = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
    def start(self):
        """Start the watchdog timer."""
        if self._running:
            return
        
        self._running = True
        self._last_ping = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Watchdog started with {self.timeout}s timeout")
    
    def stop(self):
        """Stop the watchdog timer."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
    
    def ping(self):
        """Reset the watchdog timer."""
        with self._lock:
            self._last_ping = time.time()
    
    def _run(self):
        """Watchdog monitoring loop."""
        while self._running:
            time.sleep(1.0)
            
            with self._lock:
                elapsed = time.time() - self._last_ping
            
            if elapsed > self.timeout:
                logger.error(f"Watchdog timeout! No activity for {elapsed:.1f}s")
                if self.on_timeout:
                    try:
                        self.on_timeout()
                    except Exception as e:
                        logger.error(f"Error in watchdog timeout handler: {e}")
                
                # Reset ping to avoid repeated triggers
                with self._lock:
                    self._last_ping = time.time()
