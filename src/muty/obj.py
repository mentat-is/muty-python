"""
generic objects functions
"""
from typing import Any


def close_object(closeable: Any):
    """
    calls close on the given object
    :param closeable: object implementing close()
    :return:
    """
    if closeable and hasattr(closeable, "close"):
        # call close
        closeable.close()
