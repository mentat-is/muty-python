import multiprocessing
import platform
import signal
import subprocess
import sys

import psutil

import muty.log

_logger = muty.log.internal_logger()


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
    _logger.info("running on %s ..." % (plat))
    if platform.system().lower() == "darwin":
        # by default, now python use spawn() on macos, and this would break gulp multiprocessing engine
        # anyway this is just for developing on macos, production will use linux.
        _logger.warning("setting multiprocessing to use fork!")
        multiprocessing.set_start_method("fork")

    # avoid zombies on processes exit
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
