"""logging utilities
"""

import asyncio
import logging
import os
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler
from typing import TypeVar

import coloredlogs


class MultiLineFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record).replace("\\n", "\n")
        return message


class MutyLogger:
    """
    a singleton logger class, represents a logger for the process
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        raise RuntimeError("call get_instance() instead")

    def _initialize(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._logger = MutyLogger.create()
            self.logger_file_path = None

    @classmethod
    def get_instance(cls) -> "MutyLogger":
        """
        returns the singleton instance
        """
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        returns the singleton's logger instance
        """
        return cls.get_instance()._logger

    @staticmethod
    def create(
        name: str = None, logger_file_path: str = None, level: int = None, **kwargs
    ) -> logging.Logger:
        """
        create a new logger with the given parameters

        Args:
            name (str, optional): the name of the logger. Defaults to None (uses the global Logger).
            log_to_file (str, optional): path to the log file. Defaults to None (log to stdout only)
            level (int, optional): the debug level. Defaults to logging.DEBUG.
            **kwargs: additional parameters to pass to configure_logger()
        Returns:
            logging.Logger: the new logger
        """
        return configure_logger(
            name=name, logger_file_path=logger_file_path, level=level, **kwargs
        )

    def reconfigure(
        self,
        name: str = None,
        logger_file_path: str = None,
        level: int = None,
        **kwargs,
    ) -> None:
        """
        reconfigure the process logger instance with the given parameters

        Args:
            name (str, optional): the name of the logger. Defaults to None (uses the global Logger).
            logger_file_path (str, optional): path to the logger file. Defaults to None (log to stdout only)
            level (int, optional): the debug level. Defaults to logging.DEBUG.
            **kwargs: additional parameters to pass to configure_logger()
        """
        _configure_logger(
            self._logger,
            name=name,
            logger_file_path=logger_file_path,
            level=level,
            **kwargs,            
        )


def configure_logger(
    name: str = None,
    logger_file_path: str = None,
    level: int = None,
    max_log_size_mb: int = 4,
    max_kept_log: int = 10,
    format_string: str = None,
    custom_field_styles: dict = None,
    use_multiline_formatter: bool = True,
) -> logging.Logger:
    """
    Configures a logger with the given parameters.

    Args:
        name (str, optional): The name of the logger. Defaults to None (uses the global Logger).
        logger_file_path (str, optional): The path to the logger file. Defaults to None (stdout only).
        level (logging.Level, optional): The logging level. Defaults to logging.DEBUG.
        max_log_size_mb (int, optional): The maximum size of each log file in MB. Defaults to 4.
        max_kept_log (int, optional): The maximum number of log files to keep. Defaults to 10.
        format_string (str, optional): The log format string. Defaults to None (uses default).
        custom_field_styles (dict, optional): A dictionary of custom field styles for coloredlogs. Defaults to None (ueses default).
        use_multiline_formatter (bool, optional): Whether to use a multiline formatter or not. Defaults to False.
    Returns:
        logging.Logger: The configured logger.
    """

    l: logging.Logger = logging.getLogger(name)
    return _configure_logger(
        l,
        logger_file_path=logger_file_path,
        level=level,
        max_log_size_mb=max_log_size_mb,
        max_kept_log=max_kept_log,
        format_string=format_string,
        custom_field_styles=custom_field_styles,
        use_multiline_formatter=use_multiline_formatter,
    )

def _configure_logger(
    l: logging.Logger,
    name: str = None,
    logger_file_path: str = None,
    level: int = None,
    max_log_size_mb: int = 4,
    max_kept_log: int = 10,
    format_string: str = None,
    custom_field_styles: dict = None,
    use_multiline_formatter: bool = True,
) -> logging.Logger:
    """
    Configures a logger with the given parameters.

    Args:
        l (logging.Logger): The logger to configure.
        name (str, optional): The name of the logger. Defaults to None (uses the global Logger).
        logger_file_path (str, optional): The path to the logger file. Defaults to None (stdout only).
        level (logging.Level, optional): The logging level. Defaults to logging.DEBUG.
        max_log_size_mb (int, optional): The maximum size of each log file in MB. Defaults to 4.
        max_kept_log (int, optional): The maximum number of log files to keep. Defaults to 10.
        format_string (str, optional): The log format string. Defaults to None (uses default).
        custom_field_styles (dict, optional): A dictionary of custom field styles for coloredlogs. Defaults to None (ueses default).
        use_multiline_formatter (bool, optional): Whether to use a multiline formatter or not. Defaults to False.
    Returns:
        logging.Logger: The configured logger.
    """

    level = level or logging.DEBUG    
    l.setLevel(level)    
    l.name = name or "root"

    # configure a default log format, including thread id
    log_format = (
        '%(asctime)s|%(name)s|%(task)s|%(levelname)s|%(process)d,%(thread_id)d|%(funcName)s|"%(pathname)s", line %(lineno)d|%(message)s'
        if format_string is None
        else format_string
    )
    handlers = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)

    stdout_handler.setFormatter(
        logging.Formatter(log_format)
        if not use_multiline_formatter
        else MultiLineFormatter(log_format)
    )
    
    if not _thread_id_filter in stdout_handler.filters:
        stdout_handler.addFilter(_thread_id_filter)
    if not _path_filter in stdout_handler.filters:
        stdout_handler.addFilter(_path_filter)
    if not _taskname_filter in stdout_handler.filters:
        stdout_handler.addFilter(_taskname_filter)
    
    if not stdout_handler in l.handlers:
        handlers.append(stdout_handler)

    if logger_file_path and not rotating_handler in l.handlers:
        # add a rotating file handler which breaks every 4mb, and keeps the last 10 log files
        rotating_handler = RotatingFileHandler(
            filename=logger_file_path,
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

    if custom_field_styles:
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
                fun = tb.tb_frame.f_code.co_name
                # %(funcName)s|\"%(pathname)s\", line %(lineno)d
                ex_str += '%s, "%s", line %d, %s' % (fun, filename, lineno, s)
    return ex_str
