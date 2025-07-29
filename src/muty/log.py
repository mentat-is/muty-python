"""logging utilities"""

import asyncio
import inspect
import logging
import os
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler, SysLogHandler

import coloredlogs


class MultiLineFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record).replace("\\n", "\n")
        return message


class TruncateFormatter(logging.Formatter):
    """
    a formatter that truncates log messages to a specified maximum length

    Args:
        fmt (str): log format string
        max_length (int): maximum length of the log message

    Returns:
        None

    Throws:
        ValueError: if max_length is not positive
    """

    def __init__(self, fmt: str, max_length: int = 1000) -> None:
        # NOTE: call parent constructor
        super().__init__(fmt)
        # NOTE: store max_length for truncation
        if max_length <= 0:
            raise ValueError("max_length must be positive")
        self.max_length: int = max_length

    def format(self, record: logging.LogRecord) -> str:
        # NOTE: format the message using parent formatter
        message: str = super().format(record)
        # NOTE: truncate if message is too long
        if len(message) > self.max_length:
            # NOTE: add ellipsis to indicate truncation
            message = message[: self.max_length - 3] + "..."
        return message


class MutyLogger(logging.Logger):
    """
    a singleton logger class, represents a logger for the process
    """

    def __init__(self):
        raise RuntimeError("call get_instance() instead")

    log_level = None
    logger_file_path = None

    @classmethod
    def get_instance(
        cls,
        name: str = None,
        logger_file_path: str = None,
        level: int = None,
        max_log_size_mb: int = 4,
        max_kept_log: int = 10,
        format_string: str = None,
        custom_field_styles: dict = None,
        use_multiline_formatter: bool = True,
        log_to_syslog: bool = False,
    ) -> "MutyLogger":
        """
        get the singleton logger instance, if it does not exist, create it

        Args:
            name (str, optional): the name of the logger. Defaults to None (uses the global Logger).
            logger_file_path (str, optional): path to the logger file. Defaults to None (log to stdout only), ignored if log_to_syslog is True.
            level (int, optional): the debug level. Defaults to logging.DEBUG.
            max_log_size_mb (int, optional): the maximum size of each log file in MB. Defaults to 4.
            max_kept_log (int, optional): the maximum number of log files to keep. Defaults to 10.
            format_string (str, optional): the log format string. Defaults to None (uses default).
            custom_field_styles (dict, optional): a dictionary of custom field styles for coloredlogs. Defaults to None (uses default).
            use_multiline_formatter (bool, optional): whether to use a multiline formatter or not. Defaults to False.
            log_to_syslog (bool, optional): whether to use syslog or not. Defaults to False, ignored if logger_file_path is provided.
        """
        if not hasattr(cls, "_instance"):
            if not name:
                raise ValueError("name must be provided for the first logger instance")
            cls._instance = logging.getLogger(name)

            # save the logger configuration as class variables
            cls.log_level = level
            cls.logger_file_path = logger_file_path

            cls._reconfigure(
                cls._instance,
                logger_file_path=logger_file_path,
                level=level,
                max_log_size_mb=max_log_size_mb,
                max_kept_log=max_kept_log,
                format_string=format_string,
                custom_field_styles=custom_field_styles,
                use_multiline_formatter=use_multiline_formatter,
                log_to_syslog=log_to_syslog,
            )
        return cls._instance

    @classmethod
    def _reconfigure(
        cls,
        l: logging.Logger,
        logger_file_path: str = None,
        level: int = None,
        max_log_size_mb: int = 4,
        max_kept_log: int = 10,
        format_string: str = None,
        custom_field_styles: dict = None,
        use_multiline_formatter: bool = True,
        log_to_syslog: bool = False,
        **kwargs,
    ) -> None:
        """
        reconfigure the process logger instance with the given parameters

        Args:
            name (str, optional): the name of the logger. Defaults to None (uses the global Logger).
            logger_file_path (str, optional): path to the logger file. Defaults to None (log to stdout only), cannot be used with log_to_syslog.
            level (int, optional): the debug level. Defaults to logging.DEBUG.
            max_log_size_mb (int, optional): the maximum size of each log file in MB. Defaults to 4.
            max_kept_log (int, optional): the maximum number of log files to keep. Defaults to 10.
            format_string (str, optional): the log format string. Defaults to None (uses default).
            custom_field_styles (dict, optional): a dictionary of custom field styles for coloredlogs. Defaults to None (uses default).
            use_multiline_formatter (bool, optional): whether to use a multiline formatter or not. Defaults to False.
            log_to_syslog (bool, optional): whether to use syslog or not. Defaults to False, cannot be used with logger_file_path.
            **kwargs: additional parameters to pass to configure_logger()
        """
        if log_to_syslog and logger_file_path:
            raise ValueError("syslog and logger_file_path cannot be used together")

        level = level or logging.DEBUG
        l.setLevel(level)
        l.handlers = []

        # configure a default log format, including thread id
        log_format = (
            '%(asctime)s|%(name)s|%(task)s|%(levelname)s|%(process)d,%(thread_id)d|%(funcName)s|"%(pathname)s", line %(lineno)d|%(message)s'
            if format_string is None
            else format_string
        )
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(level)
        stdout_handler.setFormatter(
            logging.Formatter(log_format)
            if not use_multiline_formatter
            else MultiLineFormatter(log_format)
        )

        if _thread_id_filter not in stdout_handler.filters:
            stdout_handler.addFilter(_thread_id_filter)
        if _path_filter not in stdout_handler.filters:
            stdout_handler.addFilter(_path_filter)
        if _taskname_filter not in stdout_handler.filters:
            stdout_handler.addFilter(_taskname_filter)

        if stdout_handler not in l.handlers:
            l.handlers.append(stdout_handler)

        if log_to_syslog:
            syslog_handler = SysLogHandler(
                address="/dev/log" if os.path.exists("/dev/log") else "/var/run/syslog",
            )
            syslog_handler.setLevel(level)
            formatter = TruncateFormatter(fmt=log_format, max_length=1000)
            syslog_handler.setFormatter(formatter)
            syslog_handler.addFilter(_thread_id_filter)
            syslog_handler.addFilter(_path_filter)
            syslog_handler.addFilter(_taskname_filter)
            if syslog_handler not in l.handlers:
                l.handlers.append(syslog_handler)
        elif logger_file_path:
            rotating_handler = RotatingFileHandler(
                filename=logger_file_path,
                maxBytes=1024 * 1000 * max_log_size_mb,
                backupCount=max_kept_log,
            )
            # add a rotating file handler which breaks every 4mb, and keeps the last 10 log files
            rotating_handler.setLevel(level)
            rotating_handler.setFormatter(logging.Formatter(log_format))
            rotating_handler.addFilter(_thread_id_filter)
            rotating_handler.addFilter(_path_filter)
            rotating_handler.addFilter(_taskname_filter)
            if rotating_handler not in l.handlers:
                l.handlers.append(rotating_handler)

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
        l.debug('logger "%s" configured!' % (l))


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

    if with_full_traceback:
        # get full traceback
        ex_str = "".join(traceback.format_exception(ex_t, ex, tb))
    else:
        if tb:
            # get only the frame causing the exception
            while tb.tb_next:
                tb = tb.tb_next
            ex_str = "".join(traceback.format_exception(ex_t, ex, tb))
        else:
            # get the caller frame
            caller_frame = inspect.currentframe().f_back
            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            fun = caller_frame.f_code.co_name
            ex_str = '%s, "%s", line %d, %s' % (fun, filename, lineno, ex)

    return ex_str
