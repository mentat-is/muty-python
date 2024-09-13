"""logging utilities
"""

import asyncio
import logging
import os
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler

import coloredlogs

_logger = None


def exception_to_string_lite(ex: Exception, back_frames: int = 2) -> str:
    frame = sys._getframe()
    for i in range(0, back_frames):
        frame = frame.f_back
    return "%s:%d:%s" % (__file__, frame.f_lineno, str(ex))


def _thread_id_filter(record) -> int:
    # get real(native) thread id in log messages
    record.thread_id = threading.get_native_id()
    return record


def _taskname_filter(record) -> int:
    # record.task = ''
    # return record
    # assign taskname if any
    try:
        l = asyncio.get_event_loop()
    except:
        # no event loop, no task
        record.task = ""
        return record

    if not l.is_running():
        record.task = ""
    else:
        try:
            task: asyncio.Task = asyncio.current_task()
            record.task = task.get_name() if task is not None else "-"
        except:
            record.task = ""
            return record

    return record


def _path_filter(record) -> int:
    # get relative path in log messages
    pathname = record.pathname
    tmp = None
    abs_sys_paths = map(os.path.abspath, sys.path)
    for path in sorted(abs_sys_paths, key=len, reverse=True):
        if not path.endswith(os.sep):
            path += os.sep
        if pathname.startswith(path):
            tmp = os.path.relpath(pathname, path)
            record.pathname = tmp
            break
    return record


def set_default_logger(l: logging.Logger):
    """
    sets a default (for muty) logger to be retrieved with get_default_logger()
    FIXME: DEPRECATED, DO NOT USE!
    :param l:
    :return:
    """
    global _logger
    _logger = l


def get_default_logger() -> logging.Logger:
    """
    returns the default logger, must be set with set_default_logger().
    FIXME: DEPRECATED, DO NOT USE!
    :raises Exception: if default logger not set
    :return:
    """
    if _logger is None:
        raise Exception("global logger not set!")
    return _logger


def internal_logger(
    log_to_file: str = None, level: int = logging.DEBUG, force_reconfigure: bool = True
) -> logging.Logger:
    """get the internal logger. if already configured (and force_reconfigure is not set), returns the existing logger.

    Args:
        log_to_file (str, optional): path to the log file. Defaults to None (log to stdout only)
        level (int, optional): the debug level. Defaults to logging.DEBUG.
        force_reconfigure (bool, optional): if True, will reconfigure the logger also if it already exists. Defaults to True.
    Returns:
        logging.Logger: configured logger
    """
    global _logger
    if _logger is not None and not force_reconfigure:
        return _logger

    _logger = configure_logger("muty", log_file=log_to_file, level=level)
    return _logger


def configure_logger(
    name: str = None,
    log_file: str = None,
    level=logging.DEBUG,
    max_log_size_mb: int = 4,
    max_kept_log: int = 10,
    format_string: str = None,
    custom_field_styles: dict = None,
) -> logging.Logger:
    """
    Configures a logger with the given parameters.

    Args:
        name (str, optional): The name of the logger. Defaults to None (uses the global Logger).
        log_file (str, optional): The path to the log file. Defaults to None (stdout only).
        level (logging.Level, optional): The logging level. Defaults to logging.DEBUG.
        max_log_size_mb (int, optional): The maximum size of each log file in MB. Defaults to 4.
        max_kept_log (int, optional): The maximum number of log files to keep. Defaults to 10.
        format_string (str, optional): The log format string. Defaults to None (uses default).
        custom_field_styles (dict, optional): A dictionary of custom field styles for coloredlogs. Defaults to None (ueses default).

    Returns:
        logging.Logger: The configured logger.
    """

    l: logging.Logger = logging.getLogger(name)
    l.setLevel(level)

    # configure a default log format, including thread id
    log_format = (
        "%(asctime)s|%(name)s|%(task)s|%(levelname)s|%(process)d,%(thread_id)d|%(pathname)s,%(funcName)s(),%(lineno)d|%(message)s"
        if format_string is None
        else format_string
    )
    handlers = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(logging.Formatter(log_format))
    stdout_handler.addFilter(_thread_id_filter)
    stdout_handler.addFilter(_path_filter)
    stdout_handler.addFilter(_taskname_filter)
    handlers.append(stdout_handler)

    if log_file is not None:
        # add a rotating file handler which breaks every 4mb, and keeps the last 10 log files
        rotating_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=1024 * 1000 * max_log_size_mb,
            backupCount=max_kept_log,
        )
        rotating_handler.setLevel(level)
        rotating_handler.setFormatter(logging.Formatter(log_format))
        rotating_handler.addFilter(_thread_id_filter)
        rotating_handler.addFilter(_path_filter)
        rotating_handler.addFilter(_taskname_filter)
        handlers.append(rotating_handler)

    # install configured logger
    l.handlers = handlers
    if custom_field_styles is None:
        # use default
        custom_field_styles = coloredlogs.DEFAULT_FIELD_STYLES
        custom_field_styles.update(
            {
                "pathname": {
                    "color": "blue",
                },
                "funcname": {
                    "color": "blue",
                },
                "lineno": {
                    "color": "yellow",
                },
                "thread_id": {
                    "color": "green",
                },
                "process": {
                    "color": "green",
                },
            }
        )

    coloredlogs.install(
        fmt=log_format,
        level=level,
        logger=l,
        milliseconds=True,
        field_styles=custom_field_styles,
    )
    # l.debug('logger "%s" configured!' % (l.name))
    return l


def exception_to_string(ex: Exception, with_full_traceback: bool = False) -> str:
    """
    Converts an exception to a string representation.

    Args:
        ex (Exception): The exception to convert.
        with_full_traceback (bool): Whether to include the full traceback or not.

    Returns:
        str: The string representation of the exception.
    """
    ex_t = ex.__class__.__name__
    tb = ex.__traceback__
    ex_str = ""

    strs = traceback.format_exception(ex_t, ex, tb if with_full_traceback else None)
    for s in strs:
        if with_full_traceback:
            ex_str += s
        else:
            if tb is None:
                ex_str += s
            else:
                filename = tb.tb_frame.f_code.co_filename
                lineno = tb.tb_lineno
                module = tb.tb_frame.f_code.co_name
                ex_str += "[%s:%s:%d] %s" % (filename, module, lineno, s)

    return ex_str
