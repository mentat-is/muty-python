"""
This module contains classes and functions for working with JSend responses.
JSend is a specification for building JSON APIs that respond in a consistent format.
For more information, see https://github.com/omniti-labs/jsend.
"""

import json
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field

import muty.log
import muty.string
import muty.time
from muty.log import MutyLogger

class JSendException(Exception):
    """
    Exception class for JSend errors.
    """

    def __init__(
        self,
        message: str = None,
        ex: Exception = None,
        req_id: str = None,
        status_code: int = 500,
    ):
        """
        Initializes the JSendException.

        Args:
            message (str, optional): The error message. Defaults to None.
            ex (Exception, optional): The originating exception object. Defaults to None.
            req_id (str, optional): The request ID. Defaults to None.
            status_code (int, optional): The HTTP status code. Defaults to 500.
        """
        self.req_id = req_id
        self.status_code = status_code
        self.err = message
        self.ex = ex

        msg: str = ""
        if message:
            msg = message
        if ex:
            msg += " (" + str(ex) + ")"

        if not msg:
            msg = "ERROR!"

        super().__init__(msg)

    def to_dict(self) -> dict:
        """
        Converts the exception to a dictionary.

        Returns:
            dict: The dictionary representation of the exception.
        """
        return error_jsend(req_id=self.req_id, err=self.err, ex=self.ex)


class JSendResponseStatus(StrEnum):
    """
    Enum for JSend response status.
    """

    SUCCESS = "success"
    PENDING = "pending"
    ERROR = "error"
    FAIL = "fail"


class JSendResponse(BaseModel):
    """
    Model for responses
    """

    status: JSendResponseStatus = Field(
        ..., description="response status", examples=[JSendResponseStatus.SUCCESS]
    )
    timestamp_msec: int = Field(
        ...,
        examples=[1692870496556],
        description="response timestamp in milliseconds from unix epoch.",
    )
    req_id: str = Field(
        None,
        examples=["the_request_id"],
        description='the same "req_id" that was sent in the request.',
    )
    data: Optional[dict] = Field(
        default=None,
        examples=[{"results": [1, 2, 3]}],
        description="depends on the response, may contain the result or error data.",
    )


def check_success(js: dict, pending_is_success: bool = True) -> bool:
    """
    Checks if a JSend response is successful.

    Args:
        js (dict): The JSend response.
        pending_is_success (bool): Whether pending status should be considered as success. Defaults to True.

    Returns:
        bool: True if the response is successful, False otherwise.
    """
    if not js:
        return False

    res = js.get("status", None)
    if not res:
        return False

    res = str(res).lower()
    if res == JSendResponseStatus.SUCCESS.value:
        return True
    if pending_is_success:
        if res == JSendResponseStatus.PENDING.value:
            return True

    return False


def success_jsend(req_id: str = None, data: dict = None) -> dict:
    """
    Creates a JSend successful dict, optionally with the given "data" node.

    Args:
        req_id (str): The request ID to be added to the response.
        data (dict): The data of the response (should contain the result itself, dict layout is API dependent). Defaults to None.

    Returns:
        dict: The JSend successful response.
    """
    js = {"status": JSendResponseStatus.SUCCESS}
    js["timestamp_msec"] = muty.time.now_msec()
    if req_id:
        js["req_id"] = req_id
    if data is not None:
        js["data"] = data

    MutyLogger.get_logger().info(json.dumps(js, indent=2))
    return js


def pending_jsend(req_id: str) -> dict:
    """
    Creates a JSend pending dict.

    Args:
        req_id (str): The request ID to be added to the response.

    Returns:
        dict: The JSend pending response.
    """
    js = {"status": "pending"}
    js["timestamp_msec"] = muty.time.now_msec()
    if req_id:
        js["req_id"] = req_id
    MutyLogger.get_logger().info(json.dumps(js, indent=2))
    return js


def error_jsend(
    req_id: str = None,
    err: str = None,
    ex: Exception = None,
    data: dict = None,
) -> dict:
    """
    Returns a dictionary in JSend format with an error status.

    Args:
        req_id (str): The request ID to be added to the response.
        err (str or dict, optional): The error message. Defaults to None.
        ex (Exception, optional): The exception object. Defaults to None.
        data (dict, optional): custom data to be added to the response. Defaults to None.
    Returns:
        dict: A dictionary in JSend format with an error status.
    """

    js = {"status": JSendResponseStatus.ERROR}
    if req_id:
        js["req_id"] = req_id
    js["timestamp_msec"] = muty.time.now_msec()
    if data:
        js["data"] = data
    else:
        js["data"] = {}

    d = js["data"]

    if err is not None:
        # custom error
        d["__message"] = err
    if ex:
        # exception info
        d["__exception"] = {
            "name": ex.__class__.__name__,
            "msg": str(ex),
            "trace": muty.log.exception_to_string(ex, with_full_traceback=True),
        }
    MutyLogger.get_logger().error(json.dumps(js, indent=2))
    return js

