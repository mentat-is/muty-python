from typing import Any


def close_object(closeable: Any):
    """
    calls close on the given object
    :param closeable: object implementing close()
    :return:
    """
    if closeable is not None:
        closeable.close()
