"""
dynamic loading of modules

TODO: module encryption/license manager
"""

import importlib
import importlib.util
import os
from types import ModuleType
import sys

def load_dynamic_module_from_file(module_name: str, path: str, add_to_sys_modules: bool = True) -> ModuleType:
    """
    Load a dynamic module from a file.

    Args:
        module_name (str): The name of the module.
        path (str): The path to the file containing the module.
        add_to_sys_modules (bool, optional): If True (default), add the module to sys.modules
        
    Returns:
        ModuleType: The loaded module.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    
    # add the module to the sys.modules dictionary (required for pickle)
    if add_to_sys_modules:
        sys.modules[module_name] = mod
    
    spec.loader.exec_module(mod)
    #print('loaded module:%s, module_name=%s' % (mod, module_name))
    return mod
