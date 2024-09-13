"""
dynamic loading of modules

TODO: module encryption/license manager
"""

import importlib
import importlib.util
import os
from types import ModuleType

import muty.log
import muty.string

_logger = muty.log.internal_logger()


def load_dynamic_module_from_file(path: str) -> ModuleType:
    """
    Load a dynamic module from a file.

    Args:
        path (str): The path to the file containing the module.

    Returns:
        ModuleType: The loaded module.
    """
    spec = importlib.util.spec_from_file_location(os.path.basename(path), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
