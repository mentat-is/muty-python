"""
time utilities
"""

import os
import time
from datetime import datetime, timedelta, timezone

import ntplib
from dateutil import parser, tz
from dateutil.parser._parser import ParserError
from muty.log import MutyLogger

MICROSECONDS_TO_NANOSECONDS = 1000
MILLISECONDS_TO_NANOSECONDS = 1000_000
SECONDS_TO_NANOSECONDS = 1000_000_000
NANOSECONDS_TO_MILLISECONDS = MILLISECONDS_TO_NANOSECONDS


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
        ("ms", 1),
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
    t = r.tx_time * 1000

    # cut the fractional part
    t = int(t)
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


def datetime_to_millis_from_unix_epoch(dt: datetime) -> int:
    """
    Converts a datetime object to milliseconds since the Unix epoch.

    Args:
        dt (datetime): Datetime object to convert.

    Returns:
        int: Milliseconds since the Unix epoch.
    """
    return int(dt.timestamp()) * 1000


def millis_from_unix_epoch_to_datetime(
    msec: int, tzn: timezone = timezone.utc
) -> datetime:
    """
    Converts milliseconds since the Unix epoch to a datetime object.

    Args:
        msec (int): Milliseconds since the Unix epoch.
        tzn (timezone, optional): Timezone to use. Defaults to timezone.utc.
    Returns:
        datetime: Datetime object.
    """
    dt = datetime.fromtimestamp(msec / 1000.0, tz=tzn)
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


def check_iso8601(s: str) -> bool:
    """
    Check if a string is a valid ISO 8601 formatted string.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a valid ISO 8601 formatted string, False otherwise.
    """
    if "T" not in s:
        # if there is no T in the string, it is not iso8601
        return False

    try:
        # attempt to parse the string as ISO 8601
        parser.isoparse(s)
        return True
    except (ParserError, ValueError):
        return False


def ensure_iso8601(
    time_str: str, dayfirst: bool = None, yearfirst: bool = None, fuzzy: bool = None
) -> str:
    """
    returns a time string in iso8601 format, starting from a string in different formats.

    formats supported:

    - iso8601
    - timestamp (seconds from epoch)
    - timestamp (milliseconds from epoch)
    - timestamp (microseconds from epoch)
    - timestamp (nanoseconds from epoch)
    - anything that dateutil.parser.parse() can handle

    Args:
        time_str (str): The input time string.
        dayfirst (bool, optional): Whether to interpret the first value in ambiguous dates as the day. Defaults to None (uses dateutil default).
        yearfirst (bool, optional): Whether to interpret the first value in ambiguous dates as the year. Defaults to None (uses dateutil default).
        fuzzy (bool, optional): Whether to interpret the string in a fuzzy way. Defaults to None (uses dateutil default).
    Returns:
        str: The ISO 8601 formatted string.
    """
    # check if time_str is in iso8601 format
    if check_iso8601(time_str):
        # MutyLogger.get_instance().warning("time_str is already in iso8601 format: %s" % (time_str))
        return time_str

    if time_str.isdigit():
        numeric = int(time_str)
        return number_to_iso8601(numeric)

    # try to parse the string as a datetime object
    dt = parser.parse(
        time_str,
        dayfirst=dayfirst,
        yearfirst=yearfirst,
        fuzzy=fuzzy,
        default=datetime.now(tz=tz.UTC),
    )
    return dt.astimezone(timezone.utc).isoformat()


def number_to_nanos_from_unix_epoch(numeric: str | int) -> int:
    """
    Converts a numeric value to nanoseconds from the Unix epoch.

    the numeric value may be in seconds/milliseconds/microseconds/nanoseconds from the unix epoch.

    Args:
        numeric (str|int): The numeric value to convert.

    Returns:
        int: The number of nanoseconds since the Unix epoch.
    """
    if isinstance(numeric, str):
        try:
            numeric = int(numeric)
        except:
            try:
                # numeric = numeric.replace(".", "")
                # numeric = int(numeric)
                s, us = divmod(float(numeric), 1.0)
                numeric = int(s) * 1_000_000_000 + round(us * 1_000_000_000)
            except:
                raise ValueError("string is not numeric")

    if numeric > 1_000_000_000_000_000_000:
        # assume nanoseconds, leave as is
        return numeric
    elif numeric > 1_000_000_000_000_000:
        # assume microseconds
        return numeric * MICROSECONDS_TO_NANOSECONDS
    elif numeric > 1_000_000_000_000:
        # assume milliseconds
        return numeric * MILLISECONDS_TO_NANOSECONDS
    elif numeric >= 0:
        # assume seconds
        return numeric * SECONDS_TO_NANOSECONDS
    else:
        raise ValueError("numeric value must be non-negative: %d" % (numeric))


def number_to_iso8601(numeric: int) -> str:
    """
    Converts a numeric value to an ISO 8601 formatted time string.

    The numeric value may be in seconds/milliseconds/microseconds/nanoseconds from the unix epoch.

    Args:
        numeric (int): The numeric value to convert.

    Returns:
        str: The ISO 8601 formatted string.
    """
    if numeric > 1_000_000_000_000_000_000:
        # assume nanoseconds
        seconds, nanoseconds = divmod(numeric, 1_000_000_000)
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc) + timedelta(
            microseconds=nanoseconds / 1000
        )
        return dt.isoformat()
    elif numeric > 1_000_000_000_000_000:
        # assume microseconds
        seconds, microseconds = divmod(numeric, 1_000_000)
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc) + timedelta(
            microseconds=microseconds
        )
        return dt.isoformat()
    elif numeric > 1_000_000_000_000:
        # assume milliseconds
        return datetime.fromtimestamp(numeric / 1_000, tz=timezone.utc).isoformat()
    elif numeric >= 0:
        # assume seconds
        return datetime.fromtimestamp(numeric, tz=timezone.utc).isoformat()
    else:
        raise ValueError("numeric value must be non-negative: %d" % (numeric))


def float_to_nanos_from_unix_epoch(f: float, utc: bool = True) -> int:
    """
    Converts a floating-point number to nanoseconds since the Unix epoch.

    Args:
        f (float): The floating-point number to convert.
        utc (bool, optional): Whether the datetime object is in UTC. Defaults to True.
    Returns:
        int: The number of nanoseconds since the Unix epoch.
    """
    dt = datetime.fromtimestamp(f, tz=timezone.utc)
    return datetime_to_nanos_from_unix_epoch(dt, utc=utc)


def datetime_to_nanos_from_unix_epoch(dt: datetime, utc: bool = True) -> int:
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


def chrome_epoch_to_iso8601(timestamp: int) -> str:
    """
    Converts a chrome timestamp to an ISO 8601 formatted string.

    Args:
        timestamp (int): timestamp to convert.

    Returns:
        str: The ISO 8601 formatted string.
    """
    epoch_start = datetime(1601, 1, 1, tzinfo=timezone.utc)
    delta = timedelta(microseconds=timestamp)
    return (epoch_start + delta).isoformat()


def chrome_epoch_to_millis_from_unix_epoch(timestamp: int) -> int:
    """
    Converts a chrome timestamp to the number of milliseconds since the Unix epoch.

    Args:
        timestamp (int): timestamp to convert.

    Returns:
        int: The number of milliseconds since the Unix epoch.
    """
    epoch_start = datetime(1601, 1, 1, tzinfo=timezone.utc)
    delta = timedelta(microseconds=timestamp)
    return int((epoch_start + delta).timestamp() * 1000)


def chrome_epoch_to_nanos_from_unix_epoch(timestamp: int):
    """
    Converts a chrome timestamp to the number of nanoseconds since the Unix epoch.
    Args:
        timestamp (int): timestamp to convert.
    Returns:
        int: The number of nanoseconds since the Unix epoch.
    """
    return chrome_epoch_to_millis_from_unix_epoch(timestamp) * 1000000

def windows_filetime_to_nanos_from_unix_epoch(timestamp: int) -> int:
    """
    Converts a Windows FILETIME timestamp to the number of nanoseconds since the Unix epoch.

    Args:
        timestamp (int): timestamp to convert.

    Returns:
        int: The number of nanoseconds since the Unix epoch.
    """
    # Windows FILETIME is in 100-nanosecond intervals since January 1, 1601 (UTC)
    # Unix epoch starts on January 1, 1970 (UTC)
    WINDOWS_TO_UNIX_EPOCH_OFFSET = 116444736000000000  # in 100-nanosecond intervals

    nanos_since_unix_epoch: int = (timestamp - WINDOWS_TO_UNIX_EPOCH_OFFSET) * 100
    return nanos_since_unix_epoch

def string_to_nanos_from_unix_epoch(
    s: str,
    utc: bool = True,
    dayfirst: bool = False,
    yearfirst: bool = True,
    fuzzy: bool = False,
) -> int:
    """
    convert an iso8601 time string to nanoseconds from the Unix epoch.

    NOTE: The string is parsed using dateutil.parser.parse(), so the valid formats are the ones listed in the dateutil documentation.

    @param s (str): The timestamp string to be converted.
    @param utc (bool, optional): Whether to use UTC timezone. Defaults to True.
    @param dayfirst (bool, optional): Whether to interpret the first value in ambiguous dates as the day. Defaults to False.
    @param yearfirst (bool, optional): Whether to interpret the first value in ambiguous dates as the year. Defaults to True.
    @param fuzzy (bool, optional): Whether to interpret the string in a fuzzy way. Defaults to False.
    @return int: The timestamp in nanoseconds from the Unix epoch.
    @throws ParserError: If the timestamp cannot be converted.
    """
    # Parse the datetime string
    try:
        dt = parser.parse(
            s,
            dayfirst=dayfirst,
            yearfirst=yearfirst,
            fuzzy=fuzzy,
            default=datetime.now(tz=tz.UTC),
        )
        # if year is before unix epoch, return epoch time in nanoseconds
        if dt.year < 1970:
            return 0

        return datetime_to_nanos_from_unix_epoch(dt, utc=utc)
    except:
        # maybe a number or float
        return number_to_nanos_from_unix_epoch(s)


def filename_to_nanos_from_unix_epoch(
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
        if time_int > 1_000_000_000_000_000_000:
            # assume nanoseconds, leave as is
            return time_int, False
        elif time_int > 1_000_000_000_000_000:
            # assoume microseconds
            return time_int * MICROSECONDS_TO_NANOSECONDS, False
        elif time_int > 1_000_000_000_000:
            # assume milliseconds
            return time_int * MILLISECONDS_TO_NANOSECONDS, False
        elif time_int >= 0:
            # else, assume seconds
            return time_int * SECONDS_TO_NANOSECONDS, False

        raise ValueError("numeric value must be non-negative: %d" % (time_int))

    try:
        ns = string_to_nanos_from_unix_epoch(
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
