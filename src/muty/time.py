"""
time utilities
"""

import os
import time
from datetime import datetime, timezone, timedelta
from dateutil import parser
import ntplib
#import pandas

SECONDS_TO_NANOSECONDS = 1000000000
NANOSECONDS_TO_MILLISECONDS = 1000000
MILLISECONDS_TO_NANOSECONDS = 1000000

def time_definition_from_milliseconds(milliseconds: float) -> str:
    """
    Converts milliseconds to a time definition string.

    Args:
        milliseconds (float): The time in milliseconds to be converted.

    Returns:
        str: The equivalent time definition string.

    Raises:
        ValueError: If the milliseconds value is negative.
    """
    if milliseconds < 0:
        raise ValueError("Milliseconds value cannot be negative.")

    time_units = [
        ("y", 31536000000),
        ("M", 2628000000),
        ("w", 604800000),
        ("d", 86400000),
        ("h", 3600000),
        ("m", 60000),
        ("s", 1000),
        ("ms", 1)
    ]

    for unit, value in time_units:
        if milliseconds >= value:
            time_value = milliseconds / value
            return f"{int(time_value)}{unit}"

    return "0ms"

def time_definition_to_milliseconds(time_str: str) -> float:
    """
    Converts a time definition string to milliseconds.

    Args:
        time_str (str): The time definition string to be converted: accepted values are "n[h|m|s|ms|d|w|M|y]" i.e. "1h", "10s", "1m", "1ms", "1w", "1M", "1y".

    Returns:
        float: The equivalent time in milliseconds.

    Raises:
        ValueError: If the time definition string is invalid.
    """
    time_str = time_str.lower()
    multiplier = {
        "ms": 1,
        "s": 1000,
        "m": 60000,
        "h": 3600000,
        "d": 86400000,
        "w": 604800000,
        "M": 2628000000,
        "y": 31536000000,
    }

    if time_str[-2:] == "ms":
        return float(time_str[:-2])
    elif time_str[-1] in multiplier:
        return float(time_str[:-1]) * multiplier[time_str[-1]]
    else:
        raise ValueError("Invalid time definition string: %s" % (time_str))


def now_ntp_msec(server: str = "pool.ntp.org") -> int:
    """
    Returns the current time in milliseconds since the Unix epoch using NTP.

    Args:
        server (str): NTP server to use. Defaults to 'pool.ntp.org'.

    Returns:
        int: Current time in milliseconds since the Unix epoch.
    """
    client = ntplib.NTPClient()
    r = client.request(server, version=3)
    t = r.orig_time * 1000
    return t


def now_msec() -> int:
    """
    Returns the current time in milliseconds since the Unix epoch using the system clock.

    Returns:
        int: Current time in milliseconds since the Unix epoch.
    """
    ms = time.time_ns() // 1_000_000
    return ms


def now_nsec() -> int:
    """
    Returns the current time in nanoseconds since the Unix epoch using the system clock.

    Returns:
        int: Current time in nanoseconds since the Unix epoch.
    """
    ns = time.time_ns()
    return ns


def datetime_to_unix_millis(dt: datetime) -> int:
    """
    Converts a datetime object to milliseconds since the Unix epoch.

    Args:
        dt (datetime): Datetime object to convert.

    Returns:
        int: Milliseconds since the Unix epoch.
    """
    return int(dt.timestamp()) * 1000


def unix_millis_to_datetime(msec: int, tz: timezone = timezone.utc) -> datetime:
    """
    Converts milliseconds since the Unix epoch to a datetime object.

    Args:
        msec (int): Milliseconds since the Unix epoch.
        tz (timezone, optional): Timezone to use. Defaults to timezone.utc.
    Returns:
        datetime: Datetime object.
    """
    dt = datetime.fromtimestamp(msec / 1000.0, tz=timezone.utc)
    return dt


def nanos_to_millis(nanos: int) -> int:
    """
    Converts nanoseconds to milliseconds.

    Args:
        nanos (int): Nanoseconds to convert.

    Returns:
        int: Milliseconds.
    """
    return nanos // NANOSECONDS_TO_MILLISECONDS

def float_to_epoch_nsec(f: float, utc: bool=True) -> int:
    """
    Converts a floating-point number to nanoseconds since the Unix epoch.

    Args:
        f (float): The floating-point number to convert.
        utc (bool, optional): Whether the datetime object is in UTC. Defaults to True.
    Returns:
        int: The number of nanoseconds since the Unix epoch.
    """
    dt=datetime.fromtimestamp(f)
    return datetime_to_epoch_nsec(dt, utc=utc)

def datetime_to_epoch_nsec(dt: datetime, utc: bool=True) -> int:
    """
    Converts a datetime object to the number of nanoseconds since the Unix epoch.
    Args:
        dt (datetime): The datetime object to convert.
        utc (bool, optional): Whether the datetime object is in UTC. Defaults to True.
    Returns:
        int: The number of nanoseconds since the Unix epoch.
    """

    if utc:
        dt = dt.astimezone(timezone.utc)

    # Calculate nanoseconds from the Unix epoch
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    nsec = int((dt - epoch).total_seconds() * 1e9)
    return nsec


def chrome_epoch_to_nanos(timestamp: int):
    """
    Converts a chrome timestamp to the number of nanoseconds since the Unix epoch.
    Args:
        timestamp (int): timestamp to convert.
    Returns:
        int: The number of nanoseconds since the Unix epoch.
    """
    epoch_start = datetime(1601, 1, 1, tzinfo=timezone.utc)
    delta = timedelta(microseconds=timestamp)
    return int((epoch_start+delta).timestamp()*1000000)*1000

def string_to_epoch_nsec(
    s: str,
    utc: bool = True,
    dayfirst: bool = False,
    yearfirst: bool = True,
) -> int:
    """
    Convert a human-readable string to nanoseconds from the Unix epoch.

    NOTE: The string is parsed using dateutil.parser.parse(), so the valid formats are the ones listed in the dateutil documentation.

    @param s (str): The timestamp string to be converted.
    @param utc (bool, optional): Whether to use UTC timezone. Defaults to True.
    @param dayfirst (bool, optional): Whether to interpret the first value in ambiguous dates as the day. Defaults to False.
    @param yearfirst (bool, optional): Whether to interpret the first value in ambiguous dates as the year. Defaults to True.
    @return int: The timestamp in nanoseconds from the Unix epoch.
    @throws ParserError: If the timestamp cannot be converted.
    """
    # Parse the datetime string
    dt = parser.parse(s, dayfirst=dayfirst, yearfirst=yearfirst)
    return datetime_to_epoch_nsec(dt, utc=utc)

def string_to_epoch_nsec_from_filepath(
    filename_or_path: str,
    separator: str = "_",
    idx: int = 0,
    utc: bool = True,
    dayfirst: bool = False,
    yearfirst: bool = True,
    fallback_to_now: bool = True,
) -> tuple[int, bool]:
    """
    Extracts a timestamp from filename/path, returning nanoseconds from unix epoch

    NOTE: The string is parsed using dateutil.parser.parse(), so the valid formats are the ones listed in the dateutil documentation.

    Args:
        filename_or_path (str): The filename or path to extract the timestamp from.
        separator (str, optional): The separator to use. Defaults to '_'.
        idx (int, optional): The index of the timestamp in the filename. Defaults to 0.
        utc (bool, optional): Whether to use UTC timezone. Defaults to True.
        dayfirst (bool, optional): Whether the day comes first in the date string. Defaults to False.
        yearfirst (bool, optional): Whether the year comes first in the date string. Defaults to True.
        fallback_to_now (bool, optional): Whether to fallback to the current time if the timestamp cannot be extracted. Defaults to True.
    Returns:
        int, bool: The extracted timestamp in nanoseconds from the Unix epoch and a boolean indicating whether the returned int is a fallback value (now() timestamp).
    Raises:
        Exception: If the timestamp cannot be extracted and fallback_to_now is False.
        ValueError: If idx is invalid.
    """
    f = os.path.basename(filename_or_path)
    parts = f.split(separator)
    if len(parts) < idx:
        raise ValueError("Invalid idx: %d" % (idx))

    timestr: str = parts[idx]
    if timestr.isnumeric():
        time_int = int(timestr)
        # check if time_int is in seconds, milliseconds, microseconds, nanoseconds. convert it to nanoseconds
        if time_int > 1_000_000_000_000:
            return time_int, False
        elif time_int > 1_000_000_000:
            return time_int * 1_000, False
        elif time_int > 1_000_000:
            return time_int * 1_000_000, False
        elif time_int > 1_000:
            return time_int * 1_000_000_000, False

    # use pandas
    try:
        ns = string_to_epoch_nsec(
            timestr,
            utc=utc,
            dayfirst=dayfirst,
            yearfirst=yearfirst,
        )
    except Exception as e:
        if fallback_to_now:
            return now_nsec(), True
        raise e

    return ns, False
