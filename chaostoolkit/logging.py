# -*- coding: utf-8 -*-
import logging
import uuid

import logzero
from logzero import LogFormatter, setup_default_logger, ForegroundColors
from pythonjsonlogger import jsonlogger

from chaostoolkit import encoder

__all__ = ["configure_logger"]


class ChaosToolkitContextFilter(logging.Filter):
    def __init__(self, name: str = '', context_id: str = None):
        logging.Filter.__init__(self, name)
        self.context_id = context_id or str(uuid.uuid4())

    def filter(self, record: logging.LogRecord) -> bool:
        record.context_id = self.context_id
        return True


def configure_logger(verbose: bool = False, log_format: str = "string",
                     log_file: str = None, logger_name: str = "chaostoolkit",
                     context_id: str = None):
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
        logging.DEBUG: ForegroundColors.CYAN,
        logging.INFO: ForegroundColors.GREEN,
        logging.WARNING: ForegroundColors.YELLOW,
        logging.ERROR: ForegroundColors.RED,
        logging.CRITICAL: ForegroundColors.RED
    }
    fmt = "%(color)s[%(asctime)s %(levelname)s]%(end_color)s %(message)s"
    if verbose:
        log_level = logging.DEBUG
        fmt = "%(color)s[%(asctime)s %(levelname)s] "\
              "[%(module)s:%(lineno)d]%(end_color)s %(message)s"

    formatter = LogFormatter(
        fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S", colors=colors)
    if log_format == 'json':
        fmt = "(process) (asctime) (levelname) (module) (lineno) (message)"
        if context_id:
            fmt = "(context_id) {}".format(fmt)
        formatter = jsonlogger.JsonFormatter(
            fmt, json_default=encoder, timestamp=True)

    logger = setup_default_logger(level=log_level, formatter=formatter)
    if context_id:
        logger.addFilter(ChaosToolkitContextFilter(logger_name, context_id))

    if log_file:
        # always everything as strings in the log file
        logger.setLevel(logging.DEBUG)
        fmt = "%(color)s[%(asctime)s %(levelname)s] "\
              "[%(module)s:%(lineno)d]%(end_color)s %(message)s"
        formatter = LogFormatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S",
                                 colors=colors)
        logzero.logfile(log_file, formatter=formatter, mode='a',
                        loglevel=logging.DEBUG)
