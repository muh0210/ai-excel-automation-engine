"""
LOGGING SYSTEM — Structured Logging for AI Excel Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Replaces print() with proper logging:
  • Rotating file handler (outputs/engine.log, 5 MB max)
  • Console handler for development
  • Per-module named loggers
"""

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
_LOG_FILE = os.path.join(_LOG_DIR, "engine.log")
_INITIALIZED = False


def _init_root():
    """Configure root logger once."""
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    os.makedirs(_LOG_DIR, exist_ok=True)

    root = logging.getLogger("ai_excel")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler — rotating, 5 MB, keep 3 backups
    fh = RotatingFileHandler(_LOG_FILE, maxBytes=5_242_880, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Console handler — INFO and above
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)


def get_logger(name):
    """
    Get a named logger under the ai_excel namespace.

    Usage:
        from utils.logger import get_logger
        log = get_logger(__name__)
        log.info("Processing %d rows", len(df))
        log.warning("Column %s has >50%% nulls", col)
        log.error("Join failed: %s", err, exc_info=True)
    """
    _init_root()
    return logging.getLogger(f"ai_excel.{name}")
