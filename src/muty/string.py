"""
String utilities.
"""

import codecs
import random
import re
import time
import uuid


def make_shorter(s: str, max_len: int = 50, ellipsis: str = "...") -> str:
    """
    Shorten a string to a maximum length, adding an ellipsis if it is shortened.

    Args:
        s (str): The input string.
        max_len (int, optional): The maximum length of the string. Defaults to 50.
        ellipsis (str, optional): The ellipsis to add if the string is shortened. Defaults to "...".

    Returns:
        str: The shortened string.
    """
    if s is None:
        return ""

    if len(s) <= max_len:
        return s
    return s[: max_len - len(ellipsis)] + ellipsis


def replace_non_alpha_characters(s: str, replace_char: str = "_") -> str:
    """
    Replaces all non-alphabetic characters in a string with a specified replacement character.

    Args:
        s (str): The input string.
        replace_char (str, optional): The character to replace non-alphabetic characters with. Defaults to '_'.

    Returns:
        str: The modified string with non-alphabetic characters replaced.
    """
    return re.sub(r"\W+", replace_char, s)


def remove_unicode_bom(s: str) -> str:
    """
    Removes the Unicode Byte Order Mark (BOM) from the beginning of a string, if present.

    Args:
        s (str): The input string.

    Returns:
        str: The string with the Unicode BOM removed, if present.
    """
    if s.startswith(codecs.BOM_UTF8.decode("utf8")):
        s = s.lstrip(codecs.BOM_UTF8.decode("utf8"))
    elif s.startswith(codecs.BOM_UTF16_LE.decode("utf-16-le")):
        s = s.lstrip(codecs.BOM_UTF16_LE.decode("utf-16-le"))
    elif s.startswith(codecs.BOM_UTF16_BE.decode("utf-16-be")):
        s = s.lstrip(codecs.BOM_UTF16_BE.decode("utf-16-be"))
    return s


def generate_unique(pre: str = None, post: str = None, use_uuid: bool = True) -> str:
    """
    Generate a unique string using either uuid4 or time + random.

    Args:
        pre (str, optional): Prefix to add to the generated string. Defaults to None.
        post (str, optional): Suffix to add to the generated string. Defaults to None.
        use_uuid (bool, optional): Whether to use uuid or time + random. Defaults to True.

    Returns:
        str: The generated unique string.
    """
    if use_uuid:
        # use the uuid lib
        ms = str(uuid.uuid4())
    else:
        # use time + random
        ms = str(time.time_ns() + random.randint(1, 64000) + random.randint(1, 64000))
    if pre is None and post is None:
        return ms

    # add pre and/or post
    s = ""
    if pre is not None:
        s += pre

    s += ms
    if post is not None:
        s += post

    return s


def escape(s: str, to_escape: list[str]) -> str:
    """
    Escape a string by replacing the characters in to_escape with their escaped counterparts.

    Args:
        s (str): The string to be escaped.
        to_escape (list[str]): The characters to be escaped.

    Returns:
        str: The escaped string.
    """
    for c in to_escape:
        s = s.replace(c, "\\" + c)
    return s


def enclose(s: str, enclosure: str = '"') -> str:
    """
    Enclose a string with a specified enclosure.

    Args:
        s (str): The string to be enclosed.
        enclosure (str, optional): The enclosure to use (default=").

    Returns:
        str: The enclosed string.
    """
    return f"{enclosure}{s}{enclosure}"
