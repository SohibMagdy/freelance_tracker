"""
crash_logger.py — Global crash diagnostics and runtime stabilization.

Captures ALL uncaught exceptions from:
  - Main thread (sys.excepthook)
  - Python threads (threading.excepthook)
  - Qt message handler (qInstallMessageHandler)
  - QThread.run() (via MonitorThread wrapper)
  - Notification subprocesses (logged on spawn failure)

Every crash is logged to logs/error.log with:
  - ISO timestamp
  - Thread name
  - Exception type + message
  - Full traceback

Also provides:
  - Watchdog heartbeat logging
  - Notification rate limiter
  - Subprocess cleanup tracker
"""

import sys
import os
import logging
import threading
import traceback
import time
import atexit
from datetime import datetime
from typing import Optional


# ==========================================
# LOG FILE SETUP
# ==========================================

def _get_log_dir() -> str:
    """Resolve the logs/ directory next to the .exe or project root."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    return os.path.join(base, "logs")


def _setup_logger() -> logging.Logger:
    """Create and configure the crash logger with file + console output."""
    log_dir = _get_log_dir()
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, "error.log")

    logger = logging.getLogger("FreelanceTracker.Crash")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if called twice
    if logger.handlers:
        return logger

    # File handler — rotating-friendly, always appends
    file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(threadName)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    # Console handler — only warnings and above
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_fmt = logging.Formatter(
        "[CrashLogger] %(levelname)s: %(message)s"
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    logger.info("=" * 70)
    logger.info("Freelance Tracker PRO - Session started at %s", datetime.now().isoformat())
    logger.info("Python %s | PID %d", sys.version.split()[0], os.getpid())
    logger.info("Log file: %s", log_path)
    logger.info("=" * 70)

    return logger


# Singleton logger instance
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Return the singleton crash logger, creating it on first call."""
    global _logger
    if _logger is None:
        _logger = _setup_logger()
    return _logger


# ==========================================
# GLOBAL EXCEPTION HOOKS
# ==========================================

def _sys_excepthook(exc_type, exc_value, exc_tb):
    """
    sys.excepthook — catches all uncaught exceptions on the main thread.
    Logs the full traceback and prevents silent termination.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    logger = get_logger()
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(
        "UNCAUGHT EXCEPTION (main thread)\n"
        "  Type: %s\n"
        "  Message: %s\n"
        "  Traceback:\n%s",
        exc_type.__name__,
        exc_value,
        tb_text,
    )


def _threading_excepthook(args):
    """
    threading.excepthook — catches uncaught exceptions in all Python threads.
    Available since Python 3.8.
    """
    if issubclass(args.exc_type, SystemExit):
        return

    logger = get_logger()
    tb_text = "".join(
        traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
    )
    thread_name = args.thread.name if args.thread else "Unknown-Thread"
    logger.critical(
        "UNCAUGHT EXCEPTION (background thread: %s)\n"
        "  Type: %s\n"
        "  Message: %s\n"
        "  Traceback:\n%s",
        thread_name,
        args.exc_type.__name__,
        args.exc_value,
        tb_text,
    )


def _qt_message_handler(msg_type, context, message):
    """
    Qt message handler — captures QtDebugMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg.
    Replaces the default handler that prints to stderr.
    """
    from PySide6.QtCore import QtMsgType

    logger = get_logger()
    location = ""
    if context.file:
        location = f" ({context.file}:{context.line})"

    if msg_type == QtMsgType.QtDebugMsg:
        logger.debug("Qt Debug%s: %s", location, message)
    elif msg_type == QtMsgType.QtInfoMsg:
        logger.info("Qt Info%s: %s", location, message)
    elif msg_type == QtMsgType.QtWarningMsg:
        logger.warning("Qt Warning%s: %s", location, message)
    elif msg_type == QtMsgType.QtCriticalMsg:
        logger.error("Qt Critical%s: %s", location, message)
    elif msg_type == QtMsgType.QtFatalMsg:
        logger.critical("Qt FATAL%s: %s", location, message)


# ==========================================
# INSTALL ALL HOOKS
# ==========================================

def install_crash_hooks():
    """
    Install all global exception hooks. Call this ONCE at application startup,
    BEFORE creating QApplication.
    """
    logger = get_logger()

    # 1. sys.excepthook — main thread
    sys.excepthook = _sys_excepthook
    logger.info("Installed sys.excepthook")

    # 2. threading.excepthook — background threads (Python 3.8+)
    if hasattr(threading, "excepthook"):
        threading.excepthook = _threading_excepthook
        logger.info("Installed threading.excepthook")

    # 3. atexit — log clean shutdowns
    atexit.register(_on_exit)
    logger.info("Installed atexit handler")

    logger.info("All crash hooks installed successfully.")


def install_qt_message_handler():
    """
    Install the Qt message handler. Call this AFTER importing PySide6
    but BEFORE creating QApplication.
    """
    try:
        from PySide6.QtCore import qInstallMessageHandler
        qInstallMessageHandler(_qt_message_handler)
        get_logger().info("Installed Qt message handler")
    except ImportError:
        get_logger().warning("PySide6 not available — Qt message handler not installed")


def _on_exit():
    """atexit handler — logs clean shutdown."""
    logger = get_logger()
    logger.info("Application exiting (atexit). Session ended at %s", datetime.now().isoformat())
    logger.info("=" * 70)


# ==========================================
# WATCHDOG HEARTBEAT
# ==========================================

class WatchdogLogger:
    """
    Periodic heartbeat logger for monitoring thread health.
    Logs every N seconds to confirm threads are alive.
    """

    def __init__(self, interval_seconds: int = 300):
        """
        Args:
            interval_seconds: How often to log a heartbeat (default 5 minutes).
        """
        self._interval = interval_seconds
        self._logger = get_logger()
        self._components: dict = {}  # name -> last_heartbeat_time
        self._lock = threading.Lock()

    def heartbeat(self, component_name: str):
        """Record a heartbeat from a named component."""
        with self._lock:
            self._components[component_name] = time.time()

    def log_status(self):
        """Log the current status of all tracked components."""
        with self._lock:
            now = time.time()
            self._logger.info("--- Watchdog Status Report ---")
            if not self._components:
                self._logger.info("  No components registered.")
            for name, last_beat in self._components.items():
                elapsed = now - last_beat
                status = "ALIVE" if elapsed < self._interval * 2 else "STALE"
                self._logger.info(
                    "  [%s] %s — last heartbeat %.1fs ago",
                    status, name, elapsed,
                )
            self._logger.info("--- End Watchdog Report ---")


# Global watchdog instance
_watchdog = WatchdogLogger()


def get_watchdog() -> WatchdogLogger:
    """Return the singleton watchdog logger."""
    return _watchdog


# ==========================================
# NOTIFICATION RATE LIMITER
# ==========================================

class NotificationRateLimiter:
    """
    Rate limiter for notifications: max 1 notification every `min_interval` seconds.
    Excess notifications are queued and drained at the allowed rate.
    Thread-safe.
    """

    def __init__(self, min_interval: float = 2.0, max_queue_size: int = 50):
        """
        Args:
            min_interval: Minimum seconds between notifications.
            max_queue_size: Maximum queued notifications before dropping oldest.
        """
        self._min_interval = min_interval
        self._max_queue_size = max_queue_size
        self._last_sent_time: float = 0.0
        self._queue: list = []
        self._lock = threading.Lock()
        self._logger = get_logger()

    def try_send(self, project: dict) -> bool:
        """
        Attempt to send a notification immediately.

        Returns:
            True if the notification can be sent now.
            False if it was queued for later.
        """
        with self._lock:
            now = time.time()
            if now - self._last_sent_time >= self._min_interval:
                self._last_sent_time = now
                return True
            else:
                # Queue it
                if len(self._queue) >= self._max_queue_size:
                    dropped = self._queue.pop(0)
                    self._logger.warning(
                        "Notification queue full (%d). Dropped oldest: %s",
                        self._max_queue_size,
                        dropped.get("title", "?")[:50],
                    )
                self._queue.append(project)
                self._logger.debug(
                    "Notification queued (queue size: %d): %s",
                    len(self._queue),
                    project.get("title", "?")[:50],
                )
                return False

    def drain_one(self) -> Optional[dict]:
        """
        Pop the next queued notification if enough time has passed.

        Returns:
            A project dict if one is ready, None otherwise.
        """
        with self._lock:
            if not self._queue:
                return None
            now = time.time()
            if now - self._last_sent_time >= self._min_interval:
                self._last_sent_time = now
                return self._queue.pop(0)
            return None

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._queue)


# ==========================================
# SUBPROCESS TRACKER
# ==========================================

class SubprocessTracker:
    """
    Track and clean up notification subprocesses.
    Prevents accumulation of zombie/orphaned processes.
    """

    def __init__(self, max_processes: int = 20):
        self._processes: list = []
        self._lock = threading.Lock()
        self._max = max_processes
        self._logger = get_logger()

    def register(self, proc) -> None:
        """Register a new subprocess for tracking."""
        with self._lock:
            self._processes.append(proc)
            self._logger.debug(
                "Subprocess registered (PID %s). Total tracked: %d",
                proc.pid, len(self._processes),
            )

    def cleanup(self) -> int:
        """
        Reap finished subprocesses and kill any excess.

        Returns:
            Number of processes cleaned up.
        """
        with self._lock:
            alive = []
            cleaned = 0

            for proc in self._processes:
                ret = proc.poll()
                if ret is not None:
                    # Process has finished
                    cleaned += 1
                else:
                    alive.append(proc)

            # Kill excess if we have too many alive
            while len(alive) > self._max:
                oldest = alive.pop(0)
                try:
                    oldest.kill()
                    oldest.wait(timeout=2)
                    cleaned += 1
                    self._logger.warning(
                        "Killed excess notification subprocess PID %s", oldest.pid
                    )
                except Exception as e:
                    self._logger.error(
                        "Failed to kill subprocess PID %s: %s", oldest.pid, e
                    )
                    alive.insert(0, oldest)  # Put it back
                    break

            self._processes = alive

            if cleaned > 0:
                self._logger.debug(
                    "Subprocess cleanup: %d reaped, %d still alive.",
                    cleaned, len(self._processes),
                )

            return cleaned

    def kill_all(self) -> None:
        """Kill all tracked subprocesses. Called on application shutdown."""
        with self._lock:
            for proc in self._processes:
                try:
                    if proc.poll() is None:
                        proc.kill()
                        proc.wait(timeout=2)
                except Exception:
                    pass
            count = len(self._processes)
            self._processes.clear()
            if count:
                self._logger.info("Killed all %d tracked subprocesses on shutdown.", count)

    @property
    def alive_count(self) -> int:
        with self._lock:
            return sum(1 for p in self._processes if p.poll() is None)


# Global instances
_rate_limiter = NotificationRateLimiter(min_interval=2.0, max_queue_size=50)
_subprocess_tracker = SubprocessTracker(max_processes=20)


def get_rate_limiter() -> NotificationRateLimiter:
    return _rate_limiter


def get_subprocess_tracker() -> SubprocessTracker:
    return _subprocess_tracker


# ==========================================
# SAFE QTHREAD RUN WRAPPER
# ==========================================

def safe_qthread_run(run_method):
    """
    Decorator for QThread.run() that catches and logs all exceptions,
    preventing silent thread death.

    Usage:
        class MyThread(QThread):
            @safe_qthread_run
            def run(self):
                ...
    """
    def wrapper(self, *args, **kwargs):
        logger = get_logger()
        thread_name = self.__class__.__name__
        try:
            return run_method(self, *args, **kwargs)
        except Exception as e:
            tb_text = traceback.format_exc()
            logger.critical(
                "UNCAUGHT EXCEPTION in QThread '%s'\n"
                "  Type: %s\n"
                "  Message: %s\n"
                "  Traceback:\n%s",
                thread_name,
                type(e).__name__,
                e,
                tb_text,
            )
            # Emit error signal if available
            if hasattr(self, "error_occurred"):
                try:
                    self.error_occurred.emit(f"FATAL: {type(e).__name__}: {e}")
                except Exception:
                    pass
    return wrapper
