import multiprocessing
import platform
import signal
import subprocess
import sys

import psutil
from importlib.metadata import PackageNotFoundError
from muty.log import MutyLogger
from importlib.metadata import version


def check_os(exclude: list = None):
    """
    Check the operating system and raise an exception if it is not supported.

    Args:
        exclude (list, optional): A list of operating systems to exclude. Defaults to None.

    Raises:
        RuntimeError: If the operating system is not supported.

    """
    if exclude is None:
        exclude = []

    if platform.system().lower() in exclude:
        raise RuntimeError("Unsupported operating system: %s" % (platform.system()))


def check_package_version(package_name: str, version_check: str = None) -> bool:
    """
    Check if a package is installed and optionally check its version.
    Supports exact match (==), version ranges (>=X.Y.Z,<=A.B.C),
    and comparisons (>, <, >=, <=).

    Args:
        package_name (str): The name of the package to check
        version_check (str, optional): Version requirement
    """

    def _parse_version(version_str: str) -> tuple:
        try:
            parts = version_str.strip().split(".")
            return tuple(int(x) for x in parts)
        except (ValueError, AttributeError):
            return tuple()

    try:
        pkg_version = version(package_name)
        if not version_check:
            return True

        pkg_tuple = _parse_version(pkg_version)
        if not pkg_tuple:
            return False

        version_check = version_check.strip()
        if "," in version_check:
            min_ver, max_ver = version_check.split(",")
            min_check, max_check = min_ver.strip(), max_ver.strip()

            meets_min = meets_max = True
            for check, comp in [(min_check, ">="), (max_check, "<=")]:
                if check.startswith(comp):
                    ver = check[2:].strip()
                    ver_tuple = _parse_version(ver)
                    if comp == ">=":
                        meets_min = ver_tuple and pkg_tuple >= ver_tuple
                    else:
                        meets_max = ver_tuple and pkg_tuple <= ver_tuple
            return meets_min and meets_max

        operators = {
            ">=": lambda x, y: x >= y,
            ">": lambda x, y: x > y,
            "<=": lambda x, y: x <= y,
            "<": lambda x, y: x < y,
        }

        for op, func in operators.items():
            if version_check.startswith(op):
                req_version = version_check[len(op) :].strip()
                req_tuple = _parse_version(req_version)
                return req_tuple and func(pkg_tuple, req_tuple)

        return pkg_version == version_check

    except (PackageNotFoundError, AttributeError, ValueError):
        return False


def check_and_install_package(package_name: str, version_check: str = None) -> None:
    """
    check if a package is installed and optionally check its version.

    if the package is not installed or has the wrong version, install it.

    Args:
        package_name (str): the name of the package to check
        version_check (str, optional): version requirement, accepts exact match (i.e. "1.0.0"), version ranges (i.e. ">=1.0.0,<2"), comparisons (i.e. ">1.0.0"). Defaults to None.
    """
    if not check_package_version(package_name, version_check):
        to_install = package_name
        if version_check:
            # check version
            if "," in version_check or any(
                op in version_check for op in [">=", ">", "<=", "<"]
            ):
                # version range or comparison
                to_install = f"{package_name}{version_check}"
            else:
                # exact version
                to_install = f"{package_name}=={version_check}"

        MutyLogger.get_instance().info(
            f"{package_name} not found or wrong version, installing {to_install} ..."
        )

        # install
        subprocess.check_call([sys.executable, "-m", "pip", "install", to_install])


def get_threads_per_core(logical=False) -> int:
    """! get number of threads per cpu core

    Args:
        logical (bool, optional): logical cores means the number of physical cores multiplied by the number of threads that can run on each core. Defaults to False.

    Returns:
        int: _description_
    """
    n = psutil.cpu_count() // psutil.cpu_count(logical=logical)
    return n


def multiprocessing_fixes():
    """! fixes for multiprocessing on macos and linux.

    namely, on macos, we need to set multiprocessing to use fork() instead of spawn().
    then we need to ignore SIGCHLD to avoid zombies on processes exit.
    """
    plat = platform.system().lower()
    MutyLogger.get_instance().info("running on %s ..." % (plat))
    if platform.system().lower() == "darwin":
        # by default, now python use spawn() on macos, and this would break gulp multiprocessing engine
        # anyway this is just for developing on macos, production will use linux.
        MutyLogger.get_instance().warning("setting multiprocessing to use fork!")
        multiprocessing.set_start_method("fork")

    # avoid zombies on processes exit
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
