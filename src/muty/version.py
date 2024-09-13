"""
This module provides functions for retrieving the version of packages.
"""

import pkg_resources


def pkg_version(name: str) -> str:
    """! Returns the version of the given package.
    :param name: package name
    :return: version of the package
    """
    return pkg_resources.get_distribution(name).version


def muty_version():
    """! Returns the version of the muty package."""
    return pkg_version("muty")
