try:
    import curses  # type: ignore
except ImportError:
    curses = None

import logging
import os
import sys
import uuid
from logging.handlers import RotatingFileHandler
from types import ModuleType
from typing import Dict

from pythonjsonlogger import jsonlogger

from chaostoolkit import encoder

if os.name == "nt":
    from colorama import init as colorama_init

    colorama_init()


__all__ = ["configure_logger"]


def inject_fake_logzero() -> None:
    """
    To remove our dependency on logzero, we need to make sure we
    take its place in the import path.
    """
    m = ModuleType("logzero")
    m.__path__ = []
    sys.modules[m.__name__] = m
    m.logger = logging.getLogger("chaostoolkit")


inject_fake_logzero()


def configure_logger(
    verbose: bool = False,
    log_format: str = "string",
    log_file: str = None,
    log_file_level: str = "debug",
    logger_name: str = "chaostoolkit",
    context_id: str = None,
):
    """
    Configure the chaostoolkit logger.

    By default logs as strings to stdout and the given file. When `log_format`
    is `"json"`, records are set to the console as JSON strings but remain
    as strings in the log file. The rationale is that the log file is mostly
    for grepping purpose while records written to the console can be forwarded
    out of band to anywhere else.
    """
    log_level = logging.INFO

    # we define colors ourselves as critical is missing in default ones
    colors = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[31m",
    }
    fmt = "%(color)s[%(asctime)s %(levelname)s]%(end_color)s %(message)s"
    if verbose:
        log_level = logging.DEBUG
        fmt = (
            "%(color)s[%(asctime)s %(levelname)s] "
            "[%(module)s:%(lineno)d]%(end_color)s %(message)s"
        )

    formatter = LogFormatter(
        fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S", colors=colors
    )
    if log_format == "json":
        if sys.version_info < (3, 8):
            fmt = "(process) (asctime) (levelname) (module) (lineno) (message)"
        else:
            fmt = "%(process) %(asctime) %(levelname) %(module) %(lineno) %(message)"
        if context_id:
            fmt = f"(context_id) {fmt}"
        formatter = jsonlogger.JsonFormatter(
            fmt, json_default=encoder, timestamp=True
        )

    logger = logging.getLogger(logger_name)
    logger.propagate = False
    logger.setLevel(log_level)

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if context_id:
        logger.addFilter(ChaosToolkitContextFilter(logger_name, context_id))

    if log_file:
        # always everything as strings in the log file
        logger.setLevel(logging.DEBUG)
        log_file_level = logging.getLevelName(log_file_level.upper())
        fmt = (
            "%(color)s[%(asctime)s %(levelname)s] "
            "[%(module)s:%(lineno)d]%(end_color)s %(message)s"
        )
        formatter = LogFormatter(
            fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S", colors=colors
        )
        handler = RotatingFileHandler(log_file)
        handler.setLevel(log_file_level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)


###############################################################################
# Private function
###############################################################################
class ChaosToolkitContextFilter(logging.Filter):
    def __init__(self, name: str = "", context_id: str = None):
        logging.Filter.__init__(self, name)
        self.context_id = context_id or str(uuid.uuid4())

    def filter(self, record: logging.LogRecord) -> bool:
        record.context_id = self.context_id
        return True


class LogFormatter(logging.Formatter):
    # adjusted from logzero
    def __init__(self, fmt: str, datefmt: str, colors: Dict[str, str]) -> None:
        logging.Formatter.__init__(self, datefmt=datefmt)

        self._fmt = fmt
        self._colors = colors
        self._normal = ""

        if colors and terminal_has_colors():
            self._normal = "\033[39m"

    def format(self, record: logging.LogRecord) -> str:
        record.asctime = self.formatTime(record, self.datefmt)
        record.message = record.getMessage()

        if record.levelno in self._colors:
            record.color = self._colors[record.levelno]
            record.end_color = self._normal
        else:
            record.color = record.end_color = ""

        formatted = self._fmt % record.__dict__

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            lines = [formatted.rstrip()]
            lines.extend(ln for ln in record.exc_text.split("\n"))
            formatted = "\n".join(lines)

        return formatted.replace("\n", "\n    ")


def terminal_has_colors() -> bool:
    # adjusted from logzero
    if os.name == "nt":
        return True

    if curses and hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                return True

        except Exception:
            pass

    return False
