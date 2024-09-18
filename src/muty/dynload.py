"""
dynamic loading of modules

TODO: module encryption/license manager
"""

import importlib
import importlib.util
import os
from types import ModuleType
import sys

def load_dynamic_module_from_file(path: str) -> ModuleType:
    """
    Load a dynamic module from a file.

    Args:
        path (str): The path to the file containing the module.

    Returns:
        ModuleType: The loaded module.
    """
    module_name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)

    # add the module to the sys.modules dictionary (required for pickle)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    #print('loaded module:%s, module_name=%s' % (mod, module_name))
    return mod
