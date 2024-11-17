import multiprocessing
import platform
import signal
import subprocess
import sys

import pkg_resources
import psutil

from muty.log import MutyLogger


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


def install_package(package: str, install_in_venv: bool = True):
    """
    Install a Python package using pip.

    DEPRECATED, use check_and_install_package instead.

    Args:
        package (str): The name of the package to install.
        install_in_venv (bool, optional): Whether to install the package in a virtual environment.
            Defaults to True.

    Raises:
        CalledProcessError: If the installation command fails.

    """
    subprocess.check_call(
        [
            sys.executable if install_in_venv else "python",
            "-m",
            "pip",
            "install",
            package,
        ]
    )

def check_package_version(package_name: str, version: str = None) -> bool:
    """
    Check if a package is installed and optionally check its version.

    Args:
        package_name (str): The name of the package to check.
        version (str, optional): The version to check. Defaults to None.

    Returns:
        bool: True if the package is installed and, optionally, has the correct version.
    """
    try:
        pkg = pkg_resources.get_distribution(package_name)
        if version:
            return pkg.version == version
        return True
    except pkg_resources.DistributionNotFound:
        return False

def check_and_install_package(package_name: str, version: str=None) -> None:
    """
    Check if a package is installed and optionally check its version. If the package is not installed or has the wrong version, install it.

    Args:
        package_name (str): The name of the package to check.
        version (str, optional): The version to check. Defaults to None.
    """
    to_install = f"{package_name}=={version}" if version else package_name
    try:
        pkg = pkg_resources.get_distribution(package_name)
        if version and pkg.version != version:
            raise pkg_resources.VersionConflict

    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
        MutyLogger.get_logger().info(f"{package_name} not found or wrong version, installing ...")
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
    MutyLogger.get_logger().info("running on %s ..." % (plat))
    if platform.system().lower() == "darwin":
        # by default, now python use spawn() on macos, and this would break gulp multiprocessing engine
        # anyway this is just for developing on macos, production will use linux.
        MutyLogger.get_logger().warning("setting multiprocessing to use fork!")
        multiprocessing.set_start_method("fork")

    # avoid zombies on processes exit
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
